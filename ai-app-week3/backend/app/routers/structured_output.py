import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    StructuredTaskDetailResponse,
    StructuredTaskExtractRequest,
    StructuredTaskExtractResponse,
    StructuredTaskRecordListResponse,
    StructuredTaskUpdateRequest,
    StructuredTaskUpdateResponse,
)
from app.services.structured_task_record_service import (
    create_structured_task_record,
    get_structured_task_record_by_id,
    list_recent_structured_task_records,
    update_structured_task_record,
)
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
async def extract_task(
    payload: StructuredTaskExtractRequest,
    db: Session = Depends(get_db),
):
    try:
        result = await extract_structured_task(payload.text)

        record = create_structured_task_record(
            db=db,
            source_text=payload.text,
            extract_result=result,
        )

        result.id = record.id
        result.created_at = record.created_at

        return result

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


@router.get(
    "/tasks/recent",
    response_model=StructuredTaskRecordListResponse,
)
def list_recent_tasks(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    records = list_recent_structured_task_records(
        db=db,
        limit=limit,
    )

    return StructuredTaskRecordListResponse(items=records)

@router.get(
    "/tasks/{task_id}",
    response_model=StructuredTaskDetailResponse,
)
def get_task_detail(
    task_id: int,
    db: Session = Depends(get_db),
):
    record = get_structured_task_record_by_id(
        db=db,
        task_id=task_id,
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="结构化任务记录不存在",
        )

    return StructuredTaskDetailResponse(item=record)


@router.patch(
    "/tasks/{task_id}",
    response_model=StructuredTaskUpdateResponse,
)
def update_task_detail(
    task_id: int,
    payload: StructuredTaskUpdateRequest,
    db: Session = Depends(get_db),
):
    record = get_structured_task_record_by_id(
        db=db,
        task_id=task_id,
    )

    if not record:
        raise HTTPException(
            status_code=404,
            detail="结构化任务记录不存在",
        )

    updated_record = update_structured_task_record(
        db=db,
        record=record,
        payload=payload,
    )

    return StructuredTaskUpdateResponse(
        success=True,
        item=updated_record,
    )