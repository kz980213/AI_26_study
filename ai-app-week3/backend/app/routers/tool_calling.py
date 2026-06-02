import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import ToolCallExecuteRequest, ToolCallExecuteResponse
from app.services.tool_calling_service import (
    ToolCallingError,
    execute_tool_call,
)

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