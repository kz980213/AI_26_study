from fastapi import APIRouter
from fastapi.responses import StreamingResponse
import asyncio
import json

router = APIRouter(prefix="/stream", tags=["stream"])


async def fake_ai_stream():
    chunks = [
        "你好，",
        "这是",
        "第3周",
        "Day4 的",
        "SSE 流式输出演示。",
        "现在你看到的是",
        "后端一段一段",
        "推送给前端的文本。",
    ]

    for index, text in enumerate(chunks):
        payload = {
            "type": "chunk",
            "index": index,
            "content": text
        }
        yield f"data: {json.dumps(payload, ensure_ascii=False)}\n\n"
        await asyncio.sleep(0.5)

    done_payload = {
        "type": "done",
        "content": "[DONE]"
    }
    yield f"data: {json.dumps(done_payload, ensure_ascii=False)}\n\n"


@router.get("/demo")
async def stream_demo():
    return StreamingResponse(
        fake_ai_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )