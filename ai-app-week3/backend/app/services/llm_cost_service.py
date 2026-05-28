from app.config import settings


def estimate_deepseek_cost_cny(
    prompt_tokens_est: int | None,
    completion_tokens_est: int | None,
) -> dict[str, float]:
    """
    根据估算 token 和 .env 中配置的单价，估算人民币成本。

    注意：
    - 这里不是精确账单
    - 单价来自 .env
    - 单位是 CNY / 1M tokens
    """

    input_tokens = prompt_tokens_est or 0
    output_tokens = completion_tokens_est or 0

    input_price = settings.DEEPSEEK_INPUT_PRICE_CNY_PER_1M_TOKENS
    output_price = settings.DEEPSEEK_OUTPUT_PRICE_CNY_PER_1M_TOKENS

    input_cost = input_tokens / 1_000_000 * input_price
    output_cost = output_tokens / 1_000_000 * output_price
    total_cost = input_cost + output_cost

    return {
        "input_cost_cny": round(input_cost, 6),
        "output_cost_cny": round(output_cost, 6),
        "total_cost_cny": round(total_cost, 6),
    }


def estimate_deepseek_cost_from_log(log) -> dict[str, float]:
    """
    从 LLMCallLog 记录中估算成本。
    """

    return estimate_deepseek_cost_cny(
        prompt_tokens_est=log.prompt_tokens_est,
        completion_tokens_est=log.completion_tokens_est,
    )