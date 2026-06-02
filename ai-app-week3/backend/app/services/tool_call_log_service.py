import json
from typing import Any, Optional

from sqlalchemy.orm import Session

from app.models import ToolCallLog


def _to_json_text(value: Optional[Any]) -> Optional[str]:
    if value is None:
        return None

    return json.dumps(
        value,
        ensure_ascii=False,
        default=str,
    )


def create_tool_call_log(
    db: Session,
    source_text: str,
    tool_name: Optional[str] = None,
    arguments: Optional[dict] = None,
    tool_result: Optional[dict] = None,
    raw_text: Optional[str] = None,
    status: str = "success",
    error_message: Optional[str] = None,
    elapsed_ms: int = 0,
    retry_count: int = 0,
) -> ToolCallLog:
    log = ToolCallLog(
        source_text=source_text,
        tool_name=tool_name,
        arguments_json=_to_json_text(arguments),
        tool_result_json=_to_json_text(tool_result),
        raw_text=raw_text,
        status=status,
        error_message=error_message,
        elapsed_ms=elapsed_ms,
        retry_count=retry_count,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log


def list_recent_tool_call_logs(
    db: Session,
    limit: int = 20,
) -> list[ToolCallLog]:
    safe_limit = min(max(limit, 1), 50)

    return (
        db.query(ToolCallLog)
        .order_by(ToolCallLog.id.desc())
        .limit(safe_limit)
        .all()
    )