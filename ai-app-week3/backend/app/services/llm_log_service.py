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
    prompt_template_name: str | None = None,
    prompt_version: str | None = None,
    system_prompt_preview: str | None = None,
) -> LLMCallLog:
    """
    保存一次 LLM 调用日志。

    Week5 Day06 新增：
    - prompt_template_name
    - prompt_version
    - system_prompt_preview
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
        prompt_template_name=prompt_template_name,
        prompt_version=prompt_version,
        system_prompt_preview=(system_prompt_preview or "")[:1000],
    )

    db.add(log)
    db.commit()
    db.refresh(log)

    return log