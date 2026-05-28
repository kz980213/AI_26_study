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
from app.config import settings
from app.services.llm_log_service import save_llm_call_log
from app.services.llm_usage_service import (
    build_prompt_text_for_estimate,
    estimate_token_count,
)
from app.services.context_service import build_limited_history_context

from app.services.prompt_service import render_chat_system_prompt


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

    Week5 Day01 新增：
    - 估算 prompt token
    - 估算 completion token
    - 保存 LLM 调用日志
    - done 事件返回模型调用信息
    """

    current_conversation_id = conversation_id or str(uuid.uuid4())
    current_request_id = request_id or str(uuid.uuid4())
    start_time = time.perf_counter()

    assistant_parts: list[str] = []

    provider = "deepseek"
    model = settings.DEEPSEEK_MODEL

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

        raw_history_messages = get_recent_chat_messages(
            db=db,
            conversation_id=current_conversation_id,
            limit=settings.LLM_MAX_HISTORY_MESSAGES + 20,
        )
    
        context_result = build_limited_history_context(
            history_messages=raw_history_messages,
            max_messages=settings.LLM_MAX_HISTORY_MESSAGES,
            max_tokens_est=settings.LLM_MAX_CONTEXT_TOKENS_EST,
        )
    
        history_messages = context_result.messages
        prompt_render = render_chat_system_prompt()
        system_prompt = prompt_render.system_prompt

        prompt_text_for_estimate = build_prompt_text_for_estimate(
            user_message=user_message,
            history_messages=history_messages,
            system_prompt=system_prompt,
        )

        prompt_tokens_est = estimate_token_count(prompt_text_for_estimate)

        yield ChatStreamEvent(
            type="start",
            message="deepseek stream started",
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            provider=provider,
            model=model,
            prompt_tokens_est=prompt_tokens_est,
            context_messages_count=context_result.selected_messages_count,
            context_tokens_est=context_result.context_tokens_est,
            truncated_messages_count=context_result.truncated_messages_count,
            prompt_template_name=prompt_render.template_name,
            prompt_version=prompt_render.version,
            system_prompt_preview=prompt_render.preview,
        )

        index = 0

        async for chunk in stream_deepseek_chat_chunks(
            user_message=user_message,
            history_messages=history_messages,
            system_prompt=system_prompt,
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

        completion_tokens_est = estimate_token_count(assistant_content)
        total_tokens_est = prompt_tokens_est + completion_tokens_est

        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        save_llm_call_log(
            db=db,
            request_id=current_request_id,
            conversation_id=current_conversation_id,
            provider=provider,
            model=model,
            status="success",
            prompt_preview=prompt_text_for_estimate,
            response_preview=assistant_content,
            prompt_tokens_est=prompt_tokens_est,
            completion_tokens_est=completion_tokens_est,
            total_tokens_est=total_tokens_est,
            elapsed_ms=elapsed_ms,
        )

        yield ChatStreamEvent(
            type="done",
            message="deepseek stream finished",
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            elapsed_ms=elapsed_ms,
            provider=provider,
            model=model,
            prompt_tokens_est=prompt_tokens_est,
            completion_tokens_est=completion_tokens_est,
            total_tokens_est=total_tokens_est,
            context_messages_count=context_result.selected_messages_count,
            context_tokens_est=context_result.context_tokens_est,
            truncated_messages_count=context_result.truncated_messages_count,
            prompt_template_name=prompt_render.template_name,
            prompt_version=prompt_render.version,
            system_prompt_preview=prompt_render.preview,
        )

    except LLMStreamError as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        prompt_text_for_estimate = user_message
        prompt_tokens_est = estimate_token_count(prompt_text_for_estimate)

        save_llm_call_log(
            db=db,
            request_id=current_request_id,
            conversation_id=current_conversation_id,
            provider=provider,
            model=model,
            status="error",
            prompt_preview=prompt_text_for_estimate,
            response_preview=None,
            prompt_tokens_est=prompt_tokens_est,
            completion_tokens_est=0,
            total_tokens_est=prompt_tokens_est,
            elapsed_ms=elapsed_ms,
            error_code=exc.error_code,
            status_code=exc.status_code,
        )

        yield ChatStreamEvent(
            type="error",
            message=exc.message,
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            error_code=exc.error_code,
            status_code=exc.status_code,
            elapsed_ms=elapsed_ms,
            provider=provider,
            model=model,
            prompt_tokens_est=prompt_tokens_est,
            completion_tokens_est=0,
            total_tokens_est=prompt_tokens_est,
        )

    except Exception as exc:
        elapsed_ms = int((time.perf_counter() - start_time) * 1000)

        prompt_tokens_est = estimate_token_count(user_message)

        save_llm_call_log(
            db=db,
            request_id=current_request_id,
            conversation_id=current_conversation_id,
            provider=provider,
            model=model,
            status="error",
            prompt_preview=user_message,
            response_preview=None,
            prompt_tokens_est=prompt_tokens_est,
            completion_tokens_est=0,
            total_tokens_est=prompt_tokens_est,
            elapsed_ms=elapsed_ms,
            error_code="UNKNOWN_STREAM_ERROR",
            status_code=None,
        )

        yield ChatStreamEvent(
            type="error",
            message=str(exc),
            conversation_id=current_conversation_id,
            request_id=current_request_id,
            error_code="UNKNOWN_STREAM_ERROR",
            elapsed_ms=elapsed_ms,
            provider=provider,
            model=model,
            prompt_tokens_est=prompt_tokens_est,
            completion_tokens_est=0,
            total_tokens_est=prompt_tokens_est,
        )

    finally:
        db.close()