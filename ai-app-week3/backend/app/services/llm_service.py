import json
from typing import AsyncGenerator

import httpx

from app.config import settings


class LLMStreamError(Exception):
    """
    大模型流式调用异常。
    """


def check_deepseek_config() -> None:
    """
    检查 DeepSeek 必要配置。
    """

    if not settings.DEEPSEEK_API_KEY:
        raise LLMStreamError("DEEPSEEK_API_KEY 未配置，请检查 backend/.env")

    if not settings.DEEPSEEK_API_URL:
        raise LLMStreamError("DEEPSEEK_API_URL 未配置，请检查 backend/.env")

    if not settings.DEEPSEEK_MODEL:
        raise LLMStreamError("DEEPSEEK_MODEL 未配置，请检查 backend/.env")


async def stream_deepseek_chat_chunks(
    user_message: str,
) -> AsyncGenerator[str, None]:
    """
    调用 DeepSeek Chat Completion 流式接口。

    这个函数只负责从 DeepSeek 拿 content chunk。
    不负责拼 SSE 协议。
    """

    check_deepseek_config()

    headers = {
        "Authorization": f"Bearer {settings.DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": settings.DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": (
                    "你是一个 AI 应用开发学习助手。"
                    "回答要简洁、具体、偏实战。"
                ),
            },
            {
                "role": "user",
                "content": user_message,
            },
        ],
        "stream": True,
        "max_tokens": 800,
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=None,
        write=10.0,
        pool=10.0,
    )

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
                    f"DeepSeek API 调用失败，status={response.status_code}, body={error_text[:500]}"
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