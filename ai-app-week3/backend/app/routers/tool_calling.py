import httpx
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import (
    ToolCallExecuteRequest,
    ToolCallExecuteResponse,
    ToolCallLogListResponse,
    ToolDefinitionListResponse,
)
from app.services.tool_call_log_service import list_recent_tool_call_logs
from app.services.tool_calling_service import (
    ToolCallingError,
    execute_tool_call,
)
from app.services.tool_registry import list_available_tools

router = APIRouter(
    prefix="/ai/tools",
    tags=["tool-calling"],
)


@router.post(
    "/execute",
    response_model=ToolCallExecuteResponse,
)
async def execute_ai_tool(
    payload: ToolCallExecuteRequest,
    db: Session = Depends(get_db),
):
    try:
        return await execute_tool_call(
            db=db,
            user_text=payload.text,
        )

    except ToolCallingError as exc:
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
    "/logs/recent",
    response_model=ToolCallLogListResponse,
)
def list_recent_logs(
    limit: int = Query(default=20, ge=1, le=50),
    db: Session = Depends(get_db),
):
    logs = list_recent_tool_call_logs(
        db=db,
        limit=limit,
    )

    return ToolCallLogListResponse(items=logs)

@router.get(
    "/available",
    response_model=ToolDefinitionListResponse,
)
def list_ai_available_tools():
    tools = list_available_tools()
    return ToolDefinitionListResponse(items=tools)