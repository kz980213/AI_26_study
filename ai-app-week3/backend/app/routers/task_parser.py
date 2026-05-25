from typing import List, Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field, validator

from app.services.structured_output import parse_requirement_to_task_json
from app.services.task_store import (
    init_ai_task_table,
    list_ai_task_records,
    save_ai_task_record,
)

router = APIRouter(prefix="/ai-tasks", tags=["ai-tasks"])

init_ai_task_table()


class ParseTaskRequest(BaseModel):
    text: str = Field(..., min_length=1, max_length=4000)


class TaskResult(BaseModel):
    title: str = Field(..., min_length=2, max_length=100)
    summary: str = Field(..., min_length=5, max_length=300)
    priority: Literal["low", "medium", "high"]
    due_in_days: int = Field(..., ge=1, le=365)
    needs_frontend: bool
    needs_backend: bool
    acceptance_criteria: List[str]
    tags: List[str] = []

    @validator("acceptance_criteria")
    def validate_acceptance_criteria(cls, value):
        if not value:
            raise ValueError("acceptance_criteria 不能为空")
        return value


@router.post("/parse")
async def parse_task(data: ParseTaskRequest):
    try:
        result = await parse_requirement_to_task_json(data.text)
        validated = TaskResult(**result["structured"])

        record_id = save_ai_task_record(
            source_text=data.text,
            result_json=validated.dict(),
            usage=result.get("usage"),
            model_name=result.get("model", ""),
        )

        return {
            "message": "解析并保存成功",
            "record_id": record_id,
            "data": validated.dict(),
            "usage": result.get("usage"),
            "model": result.get("model"),
        }
    except Exception as error:
        raise HTTPException(status_code=500, detail=str(error))


@router.get("/records")
def get_records(limit: int = Query(10, ge=1, le=50)):
    items = list_ai_task_records(limit=limit)
    return {"items": items}