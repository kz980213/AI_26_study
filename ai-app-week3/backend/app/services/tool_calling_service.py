import re
import time
from typing import Any, Optional

import httpx
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.config import settings
from app.schemas import (
    CreateTaskToolArguments,
    ListRecentTasksToolArguments,
    StructuredTask,
    StructuredTaskExtractResponse,
    ToolCallDecision,
    ToolCallExecuteResponse,
)
from app.services.structured_task_record_service import (
    create_structured_task_record,
    list_recent_structured_task_records,
)
from app.services.tool_call_log_service import create_tool_call_log

from app.services.tool_registry import ensure_allowed_tool_name


class ToolCallingError(Exception):
    def __init__(self, message: str, raw_text: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.raw_text = raw_text


def _get_setting(name: str, default: Any = None) -> Any:
    return getattr(settings, name, getattr(settings, name.lower(), default))


def _extract_json_text(content: str) -> str:
    text = content.strip()

    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise ToolCallingError(
            message="模型没有返回可解析的工具调用 JSON",
            raw_text=content,
        )

    return text[start : end + 1]


def _build_tool_call_messages(user_text: str):
    system_prompt = """
你是一个工具调用决策助手。
你的任务不是直接回答用户，而是判断应该调用哪个后端工具。

你只能选择下面两个工具之一：

工具一：create_task
用途：当用户想创建、添加、安排、提醒一个任务时使用。
arguments 格式：
{
  "title": "任务标题，必填，字符串",
  "category": "任务分类，必填，例如 学习 / 工作 / 生活 / 其他",
  "priority": "只能是 low / medium / high",
  "due_time": "截止或提醒时间，没有就返回 null",
  "description": "任务描述，没有就返回 null"
}

工具二：list_recent_tasks
用途：当用户想查看、列出、查询最近任务时使用。
arguments 格式：
{
  "limit": 5
}

你必须只返回 JSON，不要返回解释文字，不要使用 Markdown。

返回格式必须是：
{
  "tool_name": "create_task 或 list_recent_tasks",
  "arguments": {}
}

优先级转换规则：
- 高 / 紧急 / 重要 => high
- 中 / 一般 => medium
- 低 / 不急 => low
- 没有明确优先级 => medium
"""

    user_prompt = f"""
用户输入：
{user_text}

请判断应该调用哪个工具，并返回工具调用 JSON。
"""

    return [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]


def _build_repair_messages(
    user_text: str,
    raw_text: str,
    error_message: str,
):
    system_prompt = """
你是一个工具调用 JSON 修复助手。
你的任务是把不合格的工具调用 JSON 修复成合法 JSON。

你只能选择下面两个工具之一：
1. create_task
2. list_recent_tasks

合法返回格式必须是：
{
  "tool_name": "create_task 或 list_recent_tasks",
  "arguments": {}
}

create_task 的 arguments 必须是：
{
  "title": "任务标题，必填，字符串",
  "category": "任务分类，必填，字符串",
  "priority": "只能是 low / medium / high",
  "due_time": "字符串或 null",
  "description": "字符串或 null"
}

list_recent_tasks 的 arguments 必须是：
{
  "limit": 1 到 20 之间的整数
}

修复规则：
- add_task / create / new_task 都改成 create_task
- recent_tasks / query_tasks / list_tasks 都改成 list_recent_tasks
- priority 如果是 高 / 紧急 / 重要，改成 high
- priority 如果是 中 / 一般，改成 medium
- priority 如果是 低 / 不急，改成 low
- create_task 如果缺少 category，补成 "其他"
- create_task 如果缺少 priority，补成 "medium"
- create_task 如果缺少 due_time，补成 null
- create_task 如果缺少 description，补成 null
- 不允许新增其他字段
- 只返回 JSON，不要返回解释，不要使用 Markdown
"""

    user_prompt = f"""
原始用户输入：
{user_text}

上一次模型输出：
{raw_text}

后端校验错误：
{error_message}

请修复为合法工具调用 JSON。
"""

    return [
        {"role": "system", "content": system_prompt.strip()},
        {"role": "user", "content": user_prompt.strip()},
    ]


async def _call_llm(messages) -> str:
    api_key = _get_setting("DEEPSEEK_API_KEY")
    api_url = _get_setting("DEEPSEEK_API_URL")
    model = _get_setting("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        raise ToolCallingError("缺少 DEEPSEEK_API_KEY 配置")

    if not api_url:
        raise ToolCallingError("缺少 DEEPSEEK_API_URL 配置")

    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0,
        "max_tokens": 500,
        "stream": False,
        "response_format": {"type": "json_object"},
    }

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
    }

    async with httpx.AsyncClient(timeout=30) as client:
        response = await client.post(
            api_url,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()

    response_data = response.json()

    try:
        return response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise ToolCallingError(
            message="模型响应结构异常，无法读取 choices[0].message.content",
            raw_text=str(response_data),
        )


def _parse_tool_decision(raw_text: str) -> ToolCallDecision:
    json_text = _extract_json_text(raw_text)

    try:
        return ToolCallDecision.model_validate_json(json_text)
    except ValidationError as exc:
        raise ToolCallingError(
            message=f"工具调用 JSON 校验失败：{exc}",
            raw_text=raw_text,
        )


def _record_to_dict(record) -> dict:
    return {
        "id": record.id,
        "source_text": record.source_text,
        "title": record.title,
        "category": record.category,
        "priority": record.priority,
        "due_time": record.due_time,
        "description": record.description,
        "retry_count": record.retry_count,
        "elapsed_ms": record.elapsed_ms,
        "created_at": record.created_at.isoformat()
        if record.created_at
        else None,
    }


def _validate_create_task_arguments(arguments: dict) -> CreateTaskToolArguments:
    try:
        return CreateTaskToolArguments.model_validate(arguments)
    except ValidationError as exc:
        raise ToolCallingError(
            message=f"create_task 参数校验失败：{exc}",
            raw_text=str(arguments),
        )


def _validate_list_recent_tasks_arguments(
    arguments: dict,
) -> ListRecentTasksToolArguments:
    try:
        return ListRecentTasksToolArguments.model_validate(arguments)
    except ValidationError as exc:
        raise ToolCallingError(
            message=f"list_recent_tasks 参数校验失败：{exc}",
            raw_text=str(arguments),
        )


def _execute_decision(
    db: Session,
    user_text: str,
    decision: ToolCallDecision,
    raw_text: str,
    start_time: float,
    retry_count: int,
) -> ToolCallExecuteResponse:
    try:
        ensure_allowed_tool_name(decision.tool_name)
    except ValueError as exc:
        raise ToolCallingError(
            message=str(exc),
            raw_text=raw_text,
        )
    if decision.tool_name == "create_task":
        args = _validate_create_task_arguments(decision.arguments)

        task = StructuredTask(
            title=args.title,
            category=args.category,
            priority=args.priority,
            due_time=args.due_time,
            description=args.description,
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        extract_result = StructuredTaskExtractResponse(
            success=True,
            data=task,
            raw_text=raw_text,
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
        )

        record = create_structured_task_record(
            db=db,
            source_text=user_text,
            extract_result=extract_result,
        )

        tool_result = {
            "record_id": record.id,
            "created_at": record.created_at.isoformat()
            if record.created_at
            else None,
            "message": "任务已创建",
        }

        log = create_tool_call_log(
            db=db,
            source_text=user_text,
            tool_name=decision.tool_name,
            arguments=args.model_dump(),
            tool_result=tool_result,
            raw_text=raw_text,
            status="success",
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
        )

        return ToolCallExecuteResponse(
            success=True,
            tool_name=decision.tool_name,
            arguments=args.model_dump(),
            tool_result=tool_result,
            raw_text=raw_text,
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
            log_id=log.id,
        )

    if decision.tool_name == "list_recent_tasks":
        args = _validate_list_recent_tasks_arguments(decision.arguments)

        records = list_recent_structured_task_records(
            db=db,
            limit=args.limit,
        )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        tool_result = {
            "items": [_record_to_dict(record) for record in records],
            "count": len(records),
        }

        log = create_tool_call_log(
            db=db,
            source_text=user_text,
            tool_name=decision.tool_name,
            arguments=args.model_dump(),
            tool_result=tool_result,
            raw_text=raw_text,
            status="success",
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
        )

        return ToolCallExecuteResponse(
            success=True,
            tool_name=decision.tool_name,
            arguments=args.model_dump(),
            tool_result=tool_result,
            raw_text=raw_text,
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
            log_id=log.id,
        )

    raise ToolCallingError(
        message=f"不支持的工具：{decision.tool_name}",
        raw_text=raw_text,
    )


async def execute_tool_call(
    db: Session,
    user_text: str,
) -> ToolCallExecuteResponse:
    start_time = time.perf_counter()
    retry_count = 0
    latest_raw_text: Optional[str] = None

    try:
        first_raw_text = await _call_llm(
            _build_tool_call_messages(user_text)
        )
        
        latest_raw_text = first_raw_text

        try:
            decision = _parse_tool_decision(first_raw_text)

            return _execute_decision(
                db=db,
                user_text=user_text,
                decision=decision,
                raw_text=first_raw_text,
                start_time=start_time,
                retry_count=retry_count,
            )

        except ToolCallingError as first_error:
            retry_count = 1

            repair_raw_text = await _call_llm(
                _build_repair_messages(
                    user_text=user_text,
                    raw_text=first_error.raw_text or first_raw_text,
                    error_message=first_error.message,
                )
            )

            latest_raw_text = repair_raw_text
            repaired_decision = _parse_tool_decision(repair_raw_text)

            return _execute_decision(
                db=db,
                user_text=user_text,
                decision=repaired_decision,
                raw_text=repair_raw_text,
                start_time=start_time,
                retry_count=retry_count,
            )

    except ToolCallingError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        create_tool_call_log(
            db=db,
            source_text=user_text,
            tool_name=None,
            arguments=None,
            tool_result=None,
            raw_text=exc.raw_text or latest_raw_text,
            status="failed",
            error_message=exc.message,
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
        )

        raise exc