import json
from sqlalchemy.orm import Session

from app.models import EmbeddingSearchLog


def create_embedding_search_log(
    db: Session,
    *,
    query: str,
    top_k: int,
    document_id: int | None,
    only_active: bool,
    quality_status: str | None,
    score_threshold: float | None,
    result: dict,
) -> EmbeddingSearchLog:
    results = result.get("results", [])
    result_chunk_ids = [item.get("chunk_id") for item in results]

    record = EmbeddingSearchLog(
        query=query,
        top_k=top_k,
        document_id=document_id,
        only_active=only_active,
        quality_status=quality_status,
        score_threshold=score_threshold,
        total_candidates=result.get("total_candidates", 0),
        matched_after_score_filter=result.get("matched_after_score_filter", 0),
        returned_count=result.get("returned_count", 0),
        max_score=result.get("max_score"),
        min_score=result.get("min_score"),
        result_chunk_ids_json=json.dumps(result_chunk_ids, ensure_ascii=False),
        results_json=json.dumps(results, ensure_ascii=False),
        applied_filters_json=json.dumps(
            result.get("applied_filters", {}),
            ensure_ascii=False,
        ),
        elapsed_ms=result.get("elapsed_ms", 0),
    )

    db.add(record)
    db.commit()
    db.refresh(record)

    return record


def serialize_embedding_search_log(
    record: EmbeddingSearchLog,
    include_results: bool = False,
) -> dict:
    data = {
        "id": record.id,
        "query": record.query,
        "top_k": record.top_k,
        "document_id": record.document_id,
        "only_active": record.only_active,
        "quality_status": record.quality_status,
        "score_threshold": record.score_threshold,
        "total_candidates": record.total_candidates,
        "matched_after_score_filter": record.matched_after_score_filter,
        "returned_count": record.returned_count,
        "max_score": record.max_score,
        "min_score": record.min_score,
        "result_chunk_ids": json.loads(record.result_chunk_ids_json or "[]"),
        "elapsed_ms": record.elapsed_ms,
        "created_at": record.created_at,
    }

    if include_results:
        data["results"] = json.loads(record.results_json or "[]")
        data["applied_filters"] = json.loads(record.applied_filters_json or "{}")

    return data


def list_recent_embedding_search_logs(db: Session, limit: int = 20) -> list[dict]:
    limit = min(max(limit, 1), 50)

    records = (
        db.query(EmbeddingSearchLog)
        .order_by(EmbeddingSearchLog.id.desc())
        .limit(limit)
        .all()
    )

    return [
        serialize_embedding_search_log(record, include_results=False)
        for record in records
    ]


def get_embedding_search_log(db: Session, log_id: int) -> dict | None:
    record = (
        db.query(EmbeddingSearchLog)
        .filter(EmbeddingSearchLog.id == log_id)
        .first()
    )

    if not record:
        return None

    return serialize_embedding_search_log(record, include_results=True)