import math


def estimate_token_count(text: str | None) -> int:
    """
    粗略估算 token 数。

    注意：
    这不是模型厂商的精确 token 计数。
    今天先用于学习和成本意识训练。

    简化估算规则：
    - 中文：大约 1~2 个汉字接近 1 token
    - 英文：大约 4 个字符接近 1 token
    这里统一用 len(text) / 2 做保守估算。
    """

    if not text:
        return 0

    cleaned_text = text.strip()

    if not cleaned_text:
        return 0

    return max(1, math.ceil(len(cleaned_text) / 2))


def build_prompt_text_for_estimate(
    user_message: str,
    history_messages: list[dict[str, str]] | None = None,
    system_prompt: str | None = None,
) -> str:
    """
    把 system prompt、本次输入和历史上下文拼成一个文本，
    用于估算输入 token。

    注意：
    这里是估算，不是模型厂商精确 token 计数。
    """

    parts: list[str] = []

    if system_prompt:
        parts.append(f"system: {system_prompt}")

    if history_messages:
        for item in history_messages:
            role = item.get("role", "")
            content = item.get("content", "")
            parts.append(f"{role}: {content}")

    last_message = history_messages[-1] if history_messages else None

    # 如果 history_messages 里最后一条已经是当前 user_message，就不重复追加
    if user_message and not (
        last_message
        and last_message.get("role") == "user"
        and last_message.get("content") == user_message
    ):
        parts.append(f"user: {user_message}")

    return "\n".join(parts)