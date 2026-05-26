import asyncio
import json

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

router = APIRouter(prefix="/ai", tags=["AI Stream"])


async def fake_ai_stream(request: Request, prompt: str):
    """
    模拟大模型流式输出。

    现在先不用真实 LLM API，
    只模拟“后端一段一段返回文本”的效果。
    """

    chunks = [
        "你好，",
        "这是第4周 Day01 的 SSE 流式输出演示。",
        "今天我们先不接真实大模型，",
        "而是先把后端流式推送和前端实时渲染跑通。",
        "后面接 DeepSeek 或 OpenAI 时，",
        "只需要把这里的 fake chunks 替换成真实模型返回的 chunks。",
    ]

    # 先推送一条 start 消息，方便前端知道流开始了
    start_payload = {
        "type": "start",
        "prompt": prompt,
        "message": "stream started",
    }
    yield f"event: start\ndata: {json.dumps(start_payload, ensure_ascii=False)}\n\n"

    for index, text in enumerate(chunks):
        # 用户关闭页面、刷新页面时，后端可以感知断开
        if await request.is_disconnected():
            print("客户端已断开 SSE 连接")
            break

        payload = {
            "type": "chunk",
            "index": index,
            "content": text,
        }

        # SSE 格式要求：
        # event: 事件名
        # data: 数据
        # 最后必须有一个空行，也就是 \n\n
        yield f"event: message\ndata: {json.dumps(payload, ensure_ascii=False)}\n\n"

        await asyncio.sleep(0.5)

    done_payload = {
        "type": "done",
        "message": "stream finished",
    }
    yield f"event: done\ndata: {json.dumps(done_payload, ensure_ascii=False)}\n\n"


@router.get("/stream")
async def stream_demo(request: Request, prompt: str = "请演示 SSE 流式输出"):
    return StreamingResponse(
        fake_ai_stream(request=request, prompt=prompt),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            # 如果以后经过 Nginx，这个可以减少代理缓冲导致的“不流式”
            "X-Accel-Buffering": "no",
        },
    )