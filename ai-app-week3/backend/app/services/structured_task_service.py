import re
import time
from typing import Any, Optional

import httpx
from pydantic import ValidationError

from app.config import settings
from app.schemas import StructuredTask, StructuredTaskExtractResponse


class StructuredTaskExtractError(Exception):
    def __init__(self, message: str, raw_text: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.raw_text = raw_text


def _get_setting(name: str, default: Any = None) -> Any:
    """
    兼容 settings.DEEPSEEK_API_KEY / settings.deepseek_api_key 两种写法。
    """
    return getattr(settings, name, getattr(settings, name.lower(), default))


def _extract_json_text(content: str) -> str:
    """
    从模型返回内容中提取 JSON。

    兼容：
    1. 直接返回 JSON
    2. 返回 ```json ... ```
    3. 前后夹杂解释文字
    """
    text = content.strip()

    text = re.sub(r"^```json\s*", "", text)
    text = re.sub(r"^```\s*", "", text)
    text = re.sub(r"\s*```$", "", text)

    start = text.find("{")
    end = text.rfind("}")

    if start == -1 or end == -1 or end <= start:
        raise StructuredTaskExtractError(
            message="模型没有返回可解析的 JSON",
            raw_text=content,
        )

    return text[start : end + 1]


def _build_extract_messages(user_text: str):
    system_prompt = """
你是一个 AI 表单助手。
你的任务是把用户输入的一段自然语言，抽取成一个任务 JSON。

你必须只返回 JSON，不要返回解释文字，不要使用 Markdown。

JSON 字段要求：
{
  "title": "任务标题，必填，简短",
  "category": "任务分类，必填，例如 学习 / 工作 / 生活 / 其他",
  "priority": "优先级，只能是 low / medium / high",
  "due_time": "截止或提醒时间，没有就返回 null",
  "description": "任务描述，没有就返回 null"
}

优先级转换规则：
- 用户说 高 / 紧急 / 重要，返回 high
- 用户说 中 / 一般，返回 medium
- 用户说 低 / 不急，返回 low
- 用户没有明确说优先级，返回 medium
"""

    user_prompt = f"""
请把下面这段用户输入抽取成任务 JSON：

用户输入：
{user_text}
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
    """
    第二次请求：不是重新抽取，而是让模型修复上一次的非法 JSON。
    """
    system_prompt = """
你是一个 JSON 修复助手。
你的任务是把一段不合格的模型输出，修复成符合要求的 JSON。

你必须只返回 JSON，不要返回解释文字，不要使用 Markdown。

合法 JSON 格式必须是：
{
  "title": "任务标题，必填，字符串",
  "category": "任务分类，必填，字符串",
  "priority": "只能是 low / medium / high",
  "due_time": "字符串或 null",
  "description": "字符串或 null"
}

修复规则：
- 如果 priority 是 高 / 紧急 / 重要，改成 high
- 如果 priority 是 中 / 一般，改成 medium
- 如果 priority 是 低 / 不急，改成 low
- 如果 priority 缺失，补成 medium
- 如果 due_time 缺失，补成 null
- 如果 description 缺失，补成 null
- 不允许新增其他字段
"""

    user_prompt = f"""
原始用户输入：
{user_text}

上一次模型输出：
{raw_text}

后端校验错误：
{error_message}

请修复为合法 JSON。
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
        raise StructuredTaskExtractError("缺少 DEEPSEEK_API_KEY 配置")

    if not api_url:
        raise StructuredTaskExtractError("缺少 DEEPSEEK_API_URL 配置")

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
        raise StructuredTaskExtractError(
            message="模型响应结构异常，无法读取 choices[0].message.content",
            raw_text=str(response_data),
        )


def _validate_task_from_raw_text(raw_text: str) -> StructuredTask:
    """
    原始模型文本 -> JSON 字符串 -> Pydantic 对象
    """
    json_text = _extract_json_text(raw_text)

    try:
        return StructuredTask.model_validate_json(json_text)
    except ValidationError as exc:
        raise StructuredTaskExtractError(
            message=f"Pydantic 校验失败：{exc}",
            raw_text=raw_text,
        )


async def extract_structured_task(
    user_text: str,
) -> StructuredTaskExtractResponse:
    start_time = time.perf_counter()

    retry_count = 0

    # 第一次：正常抽取
    first_raw_text = await _call_llm(
        _build_extract_messages(user_text)
    )

    try:
        task = _validate_task_from_raw_text(first_raw_text)

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        return StructuredTaskExtractResponse(
            success=True,
            data=task,
            raw_text=first_raw_text,
            elapsed_ms=elapsed_ms,
            retry_count=retry_count,
        )

    except StructuredTaskExtractError as first_error:
        # 第二次：带着错误原因自动修复
        retry_count = 1

        repair_raw_text = await _call_llm(
            _build_repair_messages(
                user_text=user_text,
                raw_text=first_error.raw_text or first_raw_text,
                error_message=first_error.message,
            )
        )

        try:
            task = _validate_task_from_raw_text(repair_raw_text)

            elapsed_ms = int((time.perf_counter() - start_time) * 1000)

            return StructuredTaskExtractResponse(
                success=True,
                data=task,
                raw_text=repair_raw_text,
                elapsed_ms=elapsed_ms,
                retry_count=retry_count,
            )

        except StructuredTaskExtractError as repair_error:
            raise StructuredTaskExtractError(
                message=f"自动修复后仍然失败：{repair_error.message}",
                raw_text=repair_error.raw_text,
            )