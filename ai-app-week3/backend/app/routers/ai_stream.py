from fastapi import APIRouter, Query, Request
from fastapi.responses import StreamingResponse

from app.schemas import ChatStreamEvent
from app.services.ai_stream_service import (
    deepseek_chat_stream_events,
    fake_chat_stream_events,
    stream_event_to_sse,
)

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
):
    """
    fake 聊天式 SSE 生成器。
    """

    try:
        async for stream_event in fake_chat_stream_events(
            user_message=user_message,
            conversation_id=conversation_id,
        ):
            if await request.is_disconnected():
                print("客户端已断开 SSE 连接")
                return

            yield stream_event_to_sse(stream_event)

    except Exception as exc:
        error_event = ChatStreamEvent(
            type="error",
            message=str(exc),
        )
        yield stream_event_to_sse(error_event)


async def deepseek_stream_generator(
    request: Request,
    user_message: str,
    conversation_id: str | None = None,
):
    """
    真实 DeepSeek 聊天式 SSE 生成器。
    """

    try:
        async for stream_event in deepseek_chat_stream_events(
            user_message=user_message,
            conversation_id=conversation_id,
        ):
            if await request.is_disconnected():
                print("客户端已断开 DeepSeek SSE 连接")
                return

            yield stream_event_to_sse(stream_event)

    except Exception as exc:
        error_event = ChatStreamEvent(
            type="error",
            message=str(exc),
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

    return create_sse_response(
        chat_stream_generator(
            request=request,
            user_message=message,
            conversation_id=conversation_id,
        )
    )


@router.get("/chat/stream/deepseek")
async def deepseek_chat_stream(
    request: Request,
    message: str = Query(..., min_length=1, description="用户输入的问题"),
    conversation_id: str | None = Query(None, description="会话 ID，可选"),
):
    """
    Day04：真实 DeepSeek 流式接口。
    """

    return create_sse_response(
        deepseek_stream_generator(
            request=request,
            user_message=message,
            conversation_id=conversation_id,
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

    return create_sse_response(
        chat_stream_generator(
            request=request,
            user_message=prompt,
        )
    )