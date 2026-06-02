from sqlalchemy.orm import Session

from app.models import StructuredTaskRecord
from app.schemas import StructuredTaskExtractResponse


def create_structured_task_record(
    db: Session,
    source_text: str,
    extract_result: StructuredTaskExtractResponse,
) -> StructuredTaskRecord:
    task = extract_result.data

    record = StructuredTaskRecord(
        source_text=source_text,
        title=task.title,
        category=task.category,
        priority=task.priority,
        due_time=task.due_time,
        description=task.description,
        raw_text=extract_result.raw_text,
        retry_count=extract_result.retry_count,
        elapsed_ms=extract_result.elapsed_ms,
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def list_recent_structured_task_records(
    db: Session,
    limit: int = 20,
) -> list[StructuredTaskRecord]:
    safe_limit = min(max(limit, 1), 50)

    return (
        db.query(StructuredTaskRecord)
        .order_by(StructuredTaskRecord.id.desc())
        .limit(safe_limit)
        .all()
    )