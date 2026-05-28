from dataclasses import dataclass

from app.config import settings
from app.services.llm_usage_service import estimate_token_count


@dataclass
class ContextBuildResult:
    """
    构建后的上下文结果。
    """

    messages: list[dict[str, str]]
    context_tokens_est: int
    selected_messages_count: int
    truncated_messages_count: int


def build_limited_history_context(
    history_messages: list[dict[str, str]],
    max_messages: int | None = None,
    max_tokens_est: int | None = None,
) -> ContextBuildResult:
    """
    根据“最大历史条数”和“最大估算 token”裁剪历史上下文。

    策略：
    1. 优先保留最近消息。
    2. 从最近消息往前加。
    3. 如果超过 token 限制，就停止加入更早消息。
    4. 最后恢复为正常时间顺序。
    """

    limit_messages = max_messages or settings.LLM_MAX_HISTORY_MESSAGES
    limit_tokens = max_tokens_est or settings.LLM_MAX_CONTEXT_TOKENS_EST

    recent_messages = history_messages[-limit_messages:]

    selected_reversed: list[dict[str, str]] = []
    total_tokens = 0

    for item in reversed(recent_messages):
        role = item.get("role", "")
        content = item.get("content", "")

        message_text = f"{role}: {content}"
        message_tokens = estimate_token_count(message_text)

        if selected_reversed and total_tokens + message_tokens > limit_tokens:
            break

        selected_reversed.append(item)
        total_tokens += message_tokens

    selected_messages = list(reversed(selected_reversed))

    return ContextBuildResult(
        messages=selected_messages,
        context_tokens_est=total_tokens,
        selected_messages_count=len(selected_messages),
        truncated_messages_count=max(0, len(history_messages) - len(selected_messages)),
    )