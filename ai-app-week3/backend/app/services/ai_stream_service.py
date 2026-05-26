import asyncio
import json
import time
import uuid
from typing import Any, AsyncGenerator

from app.schemas import ChatStreamEvent
from app.services.llm_service import LLMStreamError, stream_deepseek_chat_chunks

from app.database import SessionLocal
from app.services.chat_history_service import (
    create_conversation_if_not_exists,
    get_recent_chat_messages,
    save_chat_message,
)


def pydantic_to_dict(model: Any) -> dict[str, Any]:
    """
    同时兼容 Pydantic v1 和 v2。
    """

    if hasattr(model, "model_dump"):
        return model.model_dump(exclude_none=True)

    return model.dict(exclude_none=True)


def build_sse_event(event: str, data: dict[str, Any]) -> str:
    """
    统一构造 SSE 数据格式。

    注意：最后必须有一个空行，也就是 \n\n。
    """

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_event_to_sse(stream_event: ChatStreamEvent) -> str:
    """
    把业务事件转换成 SSE 字符串。

    业务错误不要发 event: error，
    避免和 EventSource 自带的 error 事件混淆。
    """

    data = pydantic_to_dict(stream_event)

    if stream_event.type == "error":
        return build_sse_event("server_error", data)

    return build_sse_event(stream_event.type, data)


async def fake_chat_stream_events(
    user_message: str,
    conversation_id: str | None = None,
    request_id: str | None = None,
) -> AsyncGenerator[ChatStreamEvent, None]:
    """
    fake 聊天流，保留给本地测试。
    """

    current_conversation_id = conversation_id or str(uuid.uuid4())
    current_request_id = request_id or str(uuid.uuid4())
    start_time = time.perf_counter()

    yield ChatStreamEvent(
        type="start",
        message="fake stream started",
        conversation_id=current_conversation_id,
        request_id=current_request_id,
    )

    chunks = [
        "这是 fake SSE 流式输出。\n",
        "今天 Day05 的重点是错误处理、日志和重试。\n",
        "真实 DeepSeek 流式接口在 /ai/chat/stream/deepseek。",
    ]

    for index, chunk in enumerate(chunks):
        yield ChatStreamEvent(
            type="chunk",
            index=index,
            content=chunk,
            conversation_id=current_conversation_id,
            request_id=current_request_id,
        )

        await asyncio.sleep(0.4)

    elapsed_ms = int((time.perf_counter() - start_time) * 1000)

    yield ChatStreamEvent(
        type="done",
        message="fake stream finished",
        conversation_id=current_conversation_id,
        request_id=current_request_id,
        elapsed_ms=elapsed_ms,
    )


async def deepseek_chat_stream_events(
    user_message: str,
    conversation_id: str | None = None,
    request_id: str | None = None,
) -> AsyncGenerator[ChatStreamEvent, None]:
    """
    真实 DeepSeek 聊天流式事件。

    Day06 新增：
    - 创建 / 复用 conversation
    - 保存 user 消息
    - 保存 assistant 完整回复
    - 使用最近消息作为多轮上下文
    """

    current_conversation_id = conversation_id or str(uuid.uuid4())
    current_request_id = request_id or str(uuid.uuid4())
    start_time = time.perf_counter()
    assistant_parts: list[str] = []

    db = SessionLocal()

    try:
        conversation = create_conversation_if_not_exists(
            db=db,
            conversation_id=current_conversation_id,
            title=user_message[:30] or "新会话",
        )

        current_conversation_id = conversation.id

        save_chat_message(
            db=db,
            conversation_id=current_conversation_id,
            role="user",
            content=user_message,
            request_id=current_request_id,
        )

        history_messages = get_recent_chat_messages(
            db=db,
            conversation_id=current_conversation_id,
            limit=8,
        )

        yield ChatStreamEvent(
            type="start",
            message="deepseek stream started",
            conversation_id=current_conversation_id,
            request_id=current_request_id,
        )

        index = 0

        async for chunk in stream_deepseek_chat_chunks(
            user_message=user_message,
            history_messages=history_messages,
        ):
            assistant_parts.append(chunk)

            yield ChatStreamEvent(
                type="chunk",
                index=index,
                content=chunk,
                conversation_id=current_conversation_id,
                request_id=current_request_id,
            )

            index += 1

        assistant_content = "".join(assistant_parts)

        if assistant_content.strip():
            save_chat_message(
                db=db,
                conversation_id=current_conversation_id,
                role="assistant",
                content=assistant_content,
                request_id=current_request_id,
            )

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        yield ChatStreamEvent(
            type="done",
            message="deepseek stream finished",
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            elapsed_ms=elapsed_ms,
        )

    except LLMStreamError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        yield ChatStreamEvent(
            type="error",
            message=exc.message,
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            error_code=exc.error_code,
            status_code=exc.status_code,
            elapsed_ms=elapsed_ms,
        )

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        yield ChatStreamEvent(
            type="error",
            message=str(exc),
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            error_code="UNKNOWN_STREAM_ERROR",
            elapsed_ms=elapsed_ms,
        )

    finally:
        db.close()