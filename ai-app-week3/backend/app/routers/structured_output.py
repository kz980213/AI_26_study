import httpx
from fastapi import APIRouter, HTTPException

from app.schemas import StructuredTaskExtractRequest, StructuredTaskExtractResponse
from app.services.structured_task_service import (
    StructuredTaskExtractError,
    extract_structured_task,
)

router = APIRouter(
    prefix="/ai/structured",
    tags=["structured-output"],
)


@router.post(
    "/tasks/extract",
    response_model=StructuredTaskExtractResponse,
)
async def extract_task(payload: StructuredTaskExtractRequest):
    try:
        return await extract_structured_task(payload.text)

    except StructuredTaskExtractError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": exc.message,
                "raw_text": exc.raw_text,
            },
        )

    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LLM API 请求失败",
                "status_code": exc.response.status_code,
                "body": exc.response.text[:500],
            },
        )

    except httpx.RequestError as exc:
        raise HTTPException(
            status_code=502,
            detail={
                "message": "LLM API 网络请求异常",
                "error": str(exc),
            },
        )