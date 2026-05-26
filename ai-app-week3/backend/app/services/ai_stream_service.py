import asyncio
import json
import uuid
from typing import Any, AsyncGenerator

from app.schemas import ChatStreamEvent

from app.services.llm_service import stream_deepseek_chat_chunks


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

    SSE 格式必须是：
    event: xxx
    data: xxx

    注意最后必须有一个空行，也就是两个换行。
    """

    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


def stream_event_to_sse(stream_event: ChatStreamEvent) -> str:
    """
    把业务事件转换成 SSE 字符串。

    注意：
    前端不要监听 event: error，
    因为 EventSource 自己也有 error 事件。
    所以后端业务错误统一发 server_error。
    """

    data = pydantic_to_dict(stream_event)

    if stream_event.type == "error":
        return build_sse_event("server_error", data)

    return build_sse_event(stream_event.type, data)


async def fake_chat_stream_events(
    user_message: str,
    conversation_id: str | None = None,
) -> AsyncGenerator[ChatStreamEvent, None]:
    """
    模拟 AI 聊天流式事件。

    后续接真实 DeepSeek / OpenAI 时，
    可以保持这个函数的输出结构不变，
    只替换内部 chunks 来源。
    """

    current_conversation_id = conversation_id or str(uuid.uuid4())

    yield ChatStreamEvent(
        type="start",
        message="stream started",
        conversation_id=current_conversation_id,
    )

    chunks = [
        "我收到了你的问题：",
        f"「{user_message}」。\n\n",
        "今天我们把 SSE 代码整理成更接近真实项目的结构。\n",
        "后端统一事件协议，",
        "前端封装 EventSource，",
        "页面只负责展示消息。\n\n",
        "这样明天或下周接真实 LLM API 时，改动会更小。",
    ]

    for index, chunk in enumerate(chunks):
        yield ChatStreamEvent(
            type="chunk",
            index=index,
            content=chunk,
            conversation_id=current_conversation_id,
        )

        await asyncio.sleep(0.45)

    yield ChatStreamEvent(
        type="done",
        message="stream finished",
        conversation_id=current_conversation_id,
    )


async def heartbeat_events() -> AsyncGenerator[ChatStreamEvent, None]:
    """
    简单心跳事件。

    真实项目里，如果模型长时间没有返回内容，
    可以用 heartbeat 告诉前端：连接还活着。
    今天只作为结构预留。
    """

    while True:
        yield ChatStreamEvent(type="heartbeat", message="ping")
        await asyncio.sleep(10)

async def deepseek_chat_stream_events(
    user_message: str,
    conversation_id: str | None = None,
) -> AsyncGenerator[ChatStreamEvent, None]:
    """
    真实 DeepSeek 聊天流式事件。

    输入：用户问题
    输出：统一 ChatStreamEvent
    """

    current_conversation_id = conversation_id or str(uuid.uuid4())

    yield ChatStreamEvent(
        type="start",
        message="deepseek stream started",
        conversation_id=current_conversation_id,
    )

    index = 0

    try:
        async for chunk in stream_deepseek_chat_chunks(user_message):
            yield ChatStreamEvent(
                type="chunk",
                index=index,
                content=chunk,
                conversation_id=current_conversation_id,
            )

            index += 1

        yield ChatStreamEvent(
            type="done",
            message="deepseek stream finished",
            conversation_id=current_conversation_id,
        )

    except Exception as exc:
        yield ChatStreamEvent(
            type="error",
            message=str(exc),
            conversation_id=current_conversation_id,
        )