import uuid

from sqlalchemy.orm import Session

from app.models import LLMCallLog


def save_llm_call_log(
    db: Session,
    request_id: str,
    conversation_id: str | None,
    provider: str,
    model: str,
    status: str,
    prompt_preview: str | None = None,
    response_preview: str | None = None,
    prompt_tokens_est: int = 0,
    completion_tokens_est: int = 0,
    total_tokens_est: int = 0,
    elapsed_ms: int | None = None,
    error_code: str | None = None,
    status_code: int | None = None,
) -> LLMCallLog:
    """
    保存一次 LLM 调用日志。
    """

    log = LLMCallLog(
        id=str(uuid.uuid4()),
        request_id=request_id,
        conversation_id=conversation_id,
        provider=provider,
        model=model,
        status=status,
        error_code=error_code,
        status_code=status_code,
        prompt_preview=(prompt_preview or "")[:1000],
        response_preview=(response_preview or "")[:1000],
        prompt_tokens_est=prompt_tokens_est,
        completion_tokens_est=completion_tokens_est,
        total_tokens_est=total_tokens_est,
        elapsed_ms=elapsed_ms,
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log