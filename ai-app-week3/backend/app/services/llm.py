import asyncio
import json
import logging
import os
import time
from typing import AsyncGenerator

import httpx

logger = logging.getLogger(__name__)

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


def to_sse(payload: dict) -> str:
    return f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"


async def stream_chat_from_provider(
    message: str,
    user_id: str = "demo-user",
) -> AsyncGenerator[str, None]:
    if not DEEPSEEK_API_KEY:
        yield to_sse({
            "type": "error",
            "message": "缺少 DEEPSEEK_API_KEY，请先配置环境变量。",
        })
        return

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "你是一个简洁、可靠的 AI 助手，请用中文回答。"
            },
            {
                "role": "user",
                "content": message
            }
        ],
        "stream": True,
        "stream_options": {
            "include_usage": True
        },
        "temperature": 0.7,
        "user_id": user_id,
    }

    timeout = httpx.Timeout(
        connect=10.0,
        read=60.0,
        write=20.0,
        pool=60.0,
    )

    max_retries = 2
    prompt_chars = len(message)

    for attempt in range(max_retries + 1):
        answer_chars = 0
        got_any_chunk = False
        started_at = time.perf_counter()

        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                async with client.stream(
                    "POST",
                    DEEPSEEK_API_URL,
                    headers=headers,
                    json=payload,
                ) as response:
                    if response.status_code == 429:
                        raise httpx.HTTPStatusError(
                            "Rate limit exceeded",
                            request=response.request,
                            response=response,
                        )

                    response.raise_for_status()

                    yield to_sse({
                        "type": "start",
                        "model": DEEPSEEK_MODEL,
                        "attempt": attempt + 1,
                    })

                    async for raw_line in response.aiter_lines():
                        # 忽略空行与 SSE keep-alive 注释
                        if not raw_line:
                            continue
                        if raw_line.startswith(":"):
                            continue
                        if not raw_line.startswith("data:"):
                            continue

                        data = raw_line[5:].strip()

                        if data == "[DONE]":
                            elapsed_ms = int((time.perf_counter() - started_at) * 1000)
                            logger.info(
                                "LLM stream finished | model=%s prompt_chars=%s answer_chars=%s elapsed_ms=%s",
                                DEEPSEEK_MODEL,
                                prompt_chars,
                                answer_chars,
                                elapsed_ms,
                            )
                            yield to_sse({
                                "type": "done",
                                "elapsed_ms": elapsed_ms,
                            })
                            return

                        parsed = json.loads(data)

                        usage = parsed.get("usage")
                        if usage:
                            yield to_sse({
                                "type": "usage",
                                "usage": usage,
                            })

                        choices = parsed.get("choices") or []
                        if not choices:
                            continue

                        delta = choices[0].get("delta") or {}
                        content = delta.get("content") or ""
                        finish_reason = choices[0].get("finish_reason")

                        if content:
                            got_any_chunk = True
                            answer_chars += len(content)
                            yield to_sse({
                                "type": "chunk",
                                "content": content,
                            })

                        if finish_reason:
                            yield to_sse({
                                "type": "finish_reason",
                                "finish_reason": finish_reason,
                            })

        except (httpx.TimeoutException, httpx.TransportError, httpx.HTTPStatusError) as error:
            can_retry = (not got_any_chunk) and (attempt < max_retries)
            logger.warning(
                "LLM request failed | attempt=%s can_retry=%s error=%s",
                attempt + 1,
                can_retry,
                repr(error),
            )

            if can_retry:
                await asyncio.sleep(attempt + 1)
                continue

            message_text = "模型请求失败，请稍后重试。"
            if isinstance(error, httpx.HTTPStatusError) and error.response is not None:
                if error.response.status_code == 429:
                    message_text = "模型接口触发限流（429），请稍后再试。"

            yield to_sse({
                "type": "error",
                "message": message_text,
            })
            return

        except Exception as error:
            logger.exception("Unexpected LLM error: %s", repr(error))
            yield to_sse({
                "type": "error",
                "message": "后端处理模型响应时发生异常。",
            })
            return