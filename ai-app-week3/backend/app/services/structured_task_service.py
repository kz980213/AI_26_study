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
    兼容你之前 config.py 里可能使用的大写字段或小写字段。
    比如：
    settings.DEEPSEEK_API_KEY
    或
    settings.deepseek_api_key
    """
    return getattr(settings, name, getattr(settings, name.lower(), default))


def _extract_json_text(content: str) -> str:
    """
    从模型返回内容中提取 JSON。

    兼容这些情况：
    1. 直接返回 JSON
    2. 返回 ```json ... ```
    3. 前后夹了一点解释文字
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


def _build_messages(user_text: str):
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


async def extract_structured_task(
    user_text: str,
) -> StructuredTaskExtractResponse:
    start_time = time.perf_counter()

    api_key = _get_setting("DEEPSEEK_API_KEY")
    api_url = _get_setting("DEEPSEEK_API_URL")
    model = _get_setting("DEEPSEEK_MODEL", "deepseek-chat")

    if not api_key:
        raise StructuredTaskExtractError("缺少 DEEPSEEK_API_KEY 配置")

    if not api_url:
        raise StructuredTaskExtractError("缺少 DEEPSEEK_API_URL 配置")

    payload = {
        "model": model,
        "messages": _build_messages(user_text),
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
        raw_content = response_data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError):
        raise StructuredTaskExtractError(
            message="模型响应结构异常，无法读取 choices[0].message.content",
            raw_text=str(response_data),
        )

    json_text = _extract_json_text(raw_content)

    try:
        task = StructuredTask.model_validate_json(json_text)
    except ValidationError as exc:
        raise StructuredTaskExtractError(
            message=f"Pydantic 校验失败：{exc}",
            raw_text=raw_content,
        )

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    return StructuredTaskExtractResponse(
        success=True,
        data=task,
        raw_text=raw_content,
        elapsed_ms=elapsed_ms,
    )