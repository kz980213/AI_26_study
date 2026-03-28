"""文档入库路由：上传文件 → 解析 → 切分 → embedding → 存储"""
from __future__ import annotations

import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import decode_access_token
from app.models.schemas import UploadResponse
from app.services.ingestion import ingest_document

router = APIRouter(prefix="/ingest", tags=["文档入库"])
logger = logging.getLogger(__name__)

SUPPORTED_TYPES = {"pdf", "md", "markdown"}
MAX_FILE_SIZE = 50 * 1024 * 1024  # 50MB


async def _get_upload_user(token: str) -> uuid.UUID | None:
    """从 header token 中解析用户 ID"""
    user_id_str = decode_access_token(token)
    if not user_id_str:
        return None
    try:
        return uuid.UUID(user_id_str)
    except ValueError:
        return None


@router.post("/upload", response_model=UploadResponse)
async def upload_document(
    file: UploadFile = File(..., description="上传 PDF 或 Markdown 文件"),
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
):
    """上传文档并入库"""
    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in SUPPORTED_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"不支持的文件类型: {ext}，仅支持 {', '.join(SUPPORTED_TYPES)}",
        )

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_SIZE:
        raise HTTPException(status_code=400, detail=f"文件大小超过 {MAX_FILE_SIZE // 1024 // 1024}MB 限制")

    uploaded_by = await _get_upload_user(token) if token else None

    try:
        doc = await ingest_document(
            file_bytes=file_bytes,
            file_name=file.filename,
            file_type=ext,
            db=db,
            uploaded_by=uploaded_by,
        )
        await db.commit()
        return UploadResponse(
            document_id=doc.id,
            file_name=doc.file_name,
            chunk_count=doc.chunk_count,
            message=f"入库成功，共生成 {doc.chunk_count} 个文本片段",
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"文档入库失败: {e}")
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"文档入库失败: {str(e)}")
