import json
from typing import AsyncGenerator, Optional

import httpx

from app.config import settings


class LLMStreamError(Exception):
    """
    大模型流式调用异常。

    不只保存 message，还保存 error_code 和 status_code，
    方便前端展示，也方便后端排查。
    """

    def __init__(
        self,
        message: str,
        error_code: str = "LLM_STREAM_ERROR",
        status_code: Optional[int] = None,
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code


def check_deepseek_config() -> None:
    """
    检查 DeepSeek 必要配置。
    """

    if not settings.DEEPSEEK_API_KEY:
        raise LLMStreamError(
            message="DEEPSEEK_API_KEY 未配置，请检查 backend/.env",
            error_code="DEEPSEEK_API_KEY_MISSING",
        )

    if not settings.DEEPSEEK_API_URL:
        raise LLMStreamError(
            message="DEEPSEEK_API_URL 未配置，请检查 backend/.env",
            error_code="DEEPSEEK_API_URL_MISSING",
        )

    if not settings.DEEPSEEK_MODEL:
        raise LLMStreamError(
            message="DEEPSEEK_MODEL 未配置，请检查 backend/.env",
            error_code="DEEPSEEK_MODEL_MISSING",
        )


def map_deepseek_error_code(status_code: int) -> str:
    """
    把 DeepSeek 返回的 HTTP 状态码转成业务错误码。
    """

    if status_code == 400:
        return "DEEPSEEK_BAD_REQUEST"

    if status_code == 401:
        return "DEEPSEEK_UNAUTHORIZED"

    if status_code == 403:
        return "DEEPSEEK_FORBIDDEN"

    if status_code == 429:
        return "DEEPSEEK_RATE_LIMITED"

    if status_code >= 500:
        return "DEEPSEEK_UPSTREAM_ERROR"

    return "DEEPSEEK_REQUEST_FAILED"


async def stream_deepseek_chat_chunks(
    user_message: str,
    history_messages: list[dict[str, str]] | None = None,
    system_prompt: str | None = None,
) -> AsyncGenerator[str, None]:
    """
    调用 DeepSeek Chat Completion 流式接口。

    这个函数只负责拿模型返回的 content chunk，
    不负责拼接 SSE 协议。
    """

    check_deepseek_config()

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    messages = [
        {
            "role": "system",
            "content": system_prompt 
            or (
                "你是一个 AI 应用开发学习助手。"
                "回答要简洁、具体、偏实战。"
            ),
        }
    ]

    if history_messages:
        messages.extend(history_messages)
    else:
        messages.append(
            {
                "role": "user",
                "content": user_message,
            }
        )
    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": messages,
        "stream": True,
        "max_tokens": 800,
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=None,
        write=10.0,
        pool=10.0,
    )

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            async with client.stream(
                "POST",
                settings.DEEPSEEK_API_URL,
                headers=headers,
                json=payload,
            ) as response:
                if response.status_code != 200:
                    error_bytes = await response.aread()
                    error_text = error_bytes.decode("utf-8", errors="ignore")

                    raise LLMStreamError(
                        message=(
                            f"DeepSeek API 调用失败，"
                            f"status={response.status_code}, "
                            f"body={error_text[:500]}"
                        ),
                        error_code=map_deepseek_error_code(response.status_code),
                        status_code=response.status_code,
                    )

                async for line in response.aiter_lines():
                    if not line:
                        continue

                    if not line.startswith("data:"):
                        continue

                    data_text = line.removeprefix("data:").strip()

                    if data_text == "[DONE]":
                        break

                    try:
                        data = json.loads(data_text)
                    except json.JSONDecodeError:
                        continue

                    choices = data.get("choices") or []

                    if not choices:
                        continue

                    delta = choices[0].get("delta") or {}
                    content = delta.get("content")

                    if content:
                        yield content

    except httpx.TimeoutException as exc:
        raise LLMStreamError(
            message=f"DeepSeek 请求超时：{str(exc)}",
            error_code="DEEPSEEK_TIMEOUT",
        ) from exc

    except httpx.ConnectError as exc:
        raise LLMStreamError(
            message=f"DeepSeek 网络连接失败：{str(exc)}",
            error_code="DEEPSEEK_CONNECT_ERROR",
        ) from exc

    except httpx.HTTPError as exc:
        raise LLMStreamError(
            message=f"DeepSeek HTTP 请求异常：{str(exc)}",
            error_code="DEEPSEEK_HTTP_ERROR",
        ) from exc