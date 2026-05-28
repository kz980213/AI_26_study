import logging
import uuid

from fastapi import APIRouter, Query, Request, Depends
from fastapi.responses import StreamingResponse

from app.schemas import ChatStreamEvent, SaveChatMessageRequest
from app.services.ai_stream_service import (
    deepseek_chat_stream_events,
    fake_chat_stream_events,
    stream_event_to_sse,
)

from sqlalchemy.orm import Session

from app.database import get_db
from app.services.chat_history_service import (
    get_conversation_messages,
    list_recent_conversations,
    create_conversation_if_not_exists,
    save_chat_message,
)

from app.models import LLMCallLog

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Stream"])


def create_sse_response(generator):
    return StreamingResponse(
        generator,
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


async def chat_stream_generator(
    request: Request,
    user_message: str,
    conversation_id: str | None = None,
    request_id: str | None = None,
):
    """
    fake 聊天式 SSE 生成器。
    """

    current_request_id = request_id or str(uuid.uuid4())

    try:
        logger.info(
            "fake_sse_start request_id=%s message_len=%s",
            current_request_id,
            len(user_message),
        )

        async for stream_event in fake_chat_stream_events(
            user_message=user_message,
            conversation_id=conversation_id,
            request_id=current_request_id,
        ):
            if await request.is_disconnected():
                logger.info(
                    "fake_sse_client_disconnected request_id=%s",
                    current_request_id,
                )
                return

            yield stream_event_to_sse(stream_event)

        logger.info("fake_sse_done request_id=%s", current_request_id)

    except Exception as exc:
        logger.exception(
            "fake_sse_error request_id=%s error=%s",
            current_request_id,
            str(exc),
        )

        error_event = ChatStreamEvent(
            type="error",
            message=str(exc),
            request_id=current_request_id,
            error_code="FAKE_STREAM_ERROR",
        )
        yield stream_event_to_sse(error_event)


async def deepseek_stream_generator(
    request: Request,
    user_message: str,
    conversation_id: str | None = None,
    request_id: str | None = None,
):
    """
    真实 DeepSeek 聊天式 SSE 生成器。
    """

    current_request_id = request_id or str(uuid.uuid4())

    try:
        logger.info(
            "deepseek_sse_start request_id=%s message_len=%s",
            current_request_id,
            len(user_message),
        )

        async for stream_event in deepseek_chat_stream_events(
            user_message=user_message,
            conversation_id=conversation_id,
            request_id=current_request_id,
        ):
            if await request.is_disconnected():
                logger.info(
                    "deepseek_sse_client_disconnected request_id=%s",
                    current_request_id,
                )
                return

            if stream_event.type == "error":
                logger.warning(
                    "deepseek_sse_server_error request_id=%s error_code=%s status_code=%s message=%s",
                    stream_event.request_id,
                    stream_event.error_code,
                    stream_event.status_code,
                    stream_event.message,
                )

            if stream_event.type == "done":
                logger.info(
                    "deepseek_sse_done request_id=%s elapsed_ms=%s",
                    stream_event.request_id,
                    stream_event.elapsed_ms,
                )

            yield stream_event_to_sse(stream_event)

    except Exception as exc:
        logger.exception(
            "deepseek_sse_unhandled_error request_id=%s error=%s",
            current_request_id,
            str(exc),
        )

        error_event = ChatStreamEvent(
            type="error",
            message=str(exc),
            request_id=current_request_id,
            error_code="DEEPSEEK_STREAM_UNHANDLED_ERROR",
        )
        yield stream_event_to_sse(error_event)


@router.get("/chat/stream")
async def chat_stream(
    request: Request,
    message: str = Query(..., min_length=1, description="用户输入的问题"),
    conversation_id: str | None = Query(None, description="会话 ID，可选"),
):
    """
    fake 流式接口，保留给本地测试。
    """

    request_id = str(uuid.uuid4())

    return create_sse_response(
        chat_stream_generator(
            request=request,
            user_message=message,
            conversation_id=conversation_id,
            request_id=request_id,
        )
    )


@router.get("/chat/stream/deepseek")
async def deepseek_chat_stream(
    request: Request,
    message: str = Query(..., min_length=1, description="用户输入的问题"),
    conversation_id: str | None = Query(None, description="会话 ID，可选"),
):
    """
    Day05：真实 DeepSeek 流式接口，增加错误分类、日志、request_id。
    """

    request_id = str(uuid.uuid4())

    return create_sse_response(
        deepseek_stream_generator(
            request=request,
            user_message=message,
            conversation_id=conversation_id,
            request_id=request_id,
        )
    )


@router.get("/stream")
async def stream_demo(
    request: Request,
    prompt: str = Query("请演示 SSE 流式输出"),
):
    """
    兼容 Day01 的普通 SSE Demo。
    """

    request_id = str(uuid.uuid4())

    return create_sse_response(
        chat_stream_generator(
            request=request,
            user_message=prompt,
            request_id=request_id,
        )
    )

@router.get("/chat/conversations")
async def get_chat_conversations(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    获取最近会话列表。
    Day06 先作为预留接口，前端今天可不用做完整会话列表。
    """

    conversations = list_recent_conversations(db=db, limit=limit)

    return [
        {
            "id": item.id,
            "title": item.title,
            "created_at": item.created_at.isoformat() if item.created_at else None,
            "updated_at": item.updated_at.isoformat() if item.updated_at else None,
        }
        for item in conversations
    ]


@router.get("/chat/conversations/{conversation_id}/messages")
async def get_chat_conversation_messages(
    conversation_id: str,
    db: Session = Depends(get_db),
):
    """
    获取某个会话的历史消息。
    """

    messages = get_conversation_messages(
        db=db,
        conversation_id=conversation_id,
    )

    return [
        {
            "id": item.id,
            "conversation_id": item.conversation_id,
            "role": item.role,
            "content": item.content,
            "request_id": item.request_id,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in messages
    ]

@router.post("/chat/messages")
async def create_chat_message(
    payload: SaveChatMessageRequest,
    db: Session = Depends(get_db),
):
    """
    手动保存一条聊天消息。

    主要用于：
    用户点击“停止输出”时，把已经流式输出的 assistant 部分内容保存下来。
    """

    content = payload.content.strip()

    if not content:
        return {
            "saved": False,
            "message": "content is empty",
        }

    create_conversation_if_not_exists(
        db=db,
        conversation_id=payload.conversation_id,
    )

    message = save_chat_message(
        db=db,
        conversation_id=payload.conversation_id,
        role=payload.role,
        content=content,
        request_id=payload.request_id,
    )

    return {
        "saved": True,
        "id": message.id,
        "conversation_id": message.conversation_id,
        "role": message.role,
        "request_id": message.request_id,
        "created_at": message.created_at.isoformat() if message.created_at else None,
    }

@router.get("/llm/call-logs")
async def get_llm_call_logs(
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    查询最近 LLM 调用日志。

    Week5 Day01 用于验证 token 估算和耗时记录是否成功。
    """

    rows = (
        db.query(LLMCallLog)
        .order_by(LLMCallLog.created_at.desc())
        .limit(limit)
        .all()
    )

    return [
        {
            "id": item.id,
            "request_id": item.request_id,
            "conversation_id": item.conversation_id,
            "provider": item.provider,
            "model": item.model,
            "status": item.status,
            "error_code": item.error_code,
            "status_code": item.status_code,
            "prompt_tokens_est": item.prompt_tokens_est,
            "completion_tokens_est": item.completion_tokens_est,
            "total_tokens_est": item.total_tokens_est,
            "elapsed_ms": item.elapsed_ms,
            "created_at": item.created_at.isoformat() if item.created_at else None,
        }
        for item in rows
    ]