import json
import os
from typing import Any, Dict

import httpx


DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = os.getenv("DEEPSEEK_API_URL", "https://api.deepseek.com/chat/completions")
DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-v4-flash")


async def parse_requirement_to_task_json(text: str) -> Dict[str, Any]:
    if not DEEPSEEK_API_KEY:
        raise RuntimeError("缺少 DEEPSEEK_API_KEY，请先配置环境变量。")

    system_prompt = """
你是一个需求整理助手。
你必须把用户输入整理成严格的 json。
不要输出 markdown，不要输出解释，不要输出多余文字，只返回 json。

json 格式必须是：
{
  "title": "字符串，简短标题",
  "summary": "字符串，任务简述",
  "priority": "low 或 medium 或 high",
  "due_in_days": 1,
  "needs_frontend": true,
  "needs_backend": false,
  "acceptance_criteria": ["字符串1", "字符串2"],
  "tags": ["字符串1", "字符串2"]
}
""".strip()

    user_prompt = f"""
请把下面这段自然语言需求整理成 json：

{text}
""".strip()

    payload = {
        "model": DEEPSEEK_MODEL,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.2,
        "max_tokens": 800,
    }

    headers = {
        "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
        "Content-Type": "application/json",
    }

    timeout = httpx.Timeout(connect=10.0, read=60.0, write=20.0, pool=60.0)

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            DEEPSEEK_API_URL,
            headers=headers,
            json=payload,
        )
        response.raise_for_status()
        data = response.json()

    content = data["choices"][0]["message"]["content"]
    structured = json.loads(content)

    return {
        "structured": structured,
        "usage": data.get("usage"),
        "model": data.get("model", DEEPSEEK_MODEL),
    }