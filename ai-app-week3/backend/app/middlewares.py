import time
import uuid
import logging
from fastapi import Request

logger = logging.getLogger("app")

async def request_log_middleware(request: Request, call_next):
    request_id = str(uuid.uuid4())[:8]
    start = time.perf_counter()

    response = await call_next(request)

    duration_ms = (time.perf_counter() - start) * 1000
    logger.info(
        f"[request_id={request_id}] {request.method} {request.url.path} -> "
        f"{response.status_code} ({duration_ms:.2f}ms)"
    )

    response.headers["X-Request-ID"] = request_id
    return response