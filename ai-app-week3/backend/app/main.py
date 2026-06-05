from fastapi import FastAPI
from fastapi.exceptions import HTTPException as FastAPIHTTPException, RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from app.routers import health, auth, users, stream, chat, task_parser, knowledge, ai_stream, structured_output, tool_calling, documents, embeddings
from app.exceptions import http_exception_handler, validation_exception_handler
from app.database import Base, engine, SessionLocal
from app.middlewares import request_log_middleware
import logging
from app.config import settings
from app.services.db_migration_service import ensure_llm_call_log_prompt_columns

from app.services.document_migration_service import ensure_document_chunk_manage_columns


logging.basicConfig(
    level=logging.INFO,
    format="[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
)

Base.metadata.create_all(bind=engine)

db = SessionLocal()
try:
    ensure_document_chunk_manage_columns(db)
finally:
    db.close()

ensure_llm_call_log_prompt_columns()

app = FastAPI(title="AI App API", version="0.1.0")
app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_middleware(
    CORSMiddleware, 
    allow_origins=settings.CORS_ALLOW_ORIGINS,
    allow_methods=["*"], 
    allow_headers=["*"]
)
app.middleware("http")(request_log_middleware)
app.include_router(health.router)
app.include_router(auth.router)
app.include_router(users.router)
app.include_router(stream.router)
app.include_router(chat.router)
app.include_router(task_parser.router)
app.include_router(knowledge.router)
app.include_router(ai_stream.router)
app.include_router(structured_output.router)
app.include_router(tool_calling.router)
app.include_router(documents.router)
app.include_router(embeddings.router)