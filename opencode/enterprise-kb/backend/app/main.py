"""FastAPI 应用入口：注册路由和中间件"""
from __future__ import annotations

import logging
import time
import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.config import get_settings, setup_logging
from app.core.database import init_db
from app.routers import auth, chat, eval, ingest

setup_logging()
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator:
    """应用生命周期：启动时初始化数据库"""
    logger.info("应用启动中...")
    await init_db()
    logger.info("数据库初始化完成")
    yield
    logger.info("应用关闭")


app = FastAPI(
    title="Enterprise Knowledge Base Q&A",
    description="企业知识库问答系统 API",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS 中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# 请求耗时日志中间件
@app.middleware("http")
async def log_request_time(request: Request, call_next):
    start = time.time()
    trace_id = str(uuid.uuid4())[:8]
    request.state.trace_id = trace_id

    response = await call_next(request)
    elapsed = int((time.time() - start) * 1000)
    logger.info(
        f"trace_id={trace_id} method={request.method} "
        f"path={request.url.path} status={response.status_code} "
        f"耗时={elapsed}ms"
    )
    response.headers["X-Trace-Id"] = trace_id
    return response


# 全局异常处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"未处理异常: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "服务器内部错误，请稍后重试"},
    )


# 注册路由
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(ingest.router)
app.include_router(eval.router)


@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "ok", "version": "1.0.0"}
