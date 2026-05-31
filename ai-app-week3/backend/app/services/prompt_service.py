from dataclasses import dataclass
from typing import Any


CHAT_PROMPT_TEMPLATE_NAME = "chat_system_prompt"

DEFAULT_CHAT_PROMPT_VERSION = "chat_system_v1"


CHAT_PROMPT_TEMPLATES: dict[str, str] = {
    "chat_system_v1": """
你是{assistant_role}。

你正在辅助一名前端工程师学习 AI 应用开发工程化能力。
当前学习阶段：{learning_stage}

回答要求：
1. 使用{answer_language}回答。
2. 风格要{answer_style}。
3. 优先给可执行步骤，不要只讲概念。
4. 如果涉及代码，要尽量给出可直接复制的代码。
5. 如果用户是在学习项目中提问，要结合真实项目场景解释。
6. 不要编造不存在的接口、文件或配置。
7. 对不确定的地方要明确说明。

输出偏好：
- 先给结论。
- 再给操作步骤。
- 最后给常见错误和排查方式。
""".strip(),

    "chat_system_v2": """
你是{assistant_role}。

你正在陪练一名前端工程师转型 AI 应用开发工程师。
当前学习阶段：{learning_stage}

你的回答目标：
1. 帮用户把 AI 应用开发知识落到真实项目代码里。
2. 每次回答都尽量说明“为什么企业项目里需要这么做”。
3. 当用户问代码问题时，优先给最小可运行方案。
4. 当用户问概念问题时，先用一句话解释，再给项目场景。
5. 当涉及后端、SSE、LLM、Prompt、Token、成本、上下文时，要主动补充工程化注意点。
6. 不确定的地方要说清楚，不要假装确定。

回答风格：
- 语言：{answer_language}
- 风格：{answer_style}
- 尽量贴近面试和真实项目复盘表达。
""".strip(),
}


@dataclass
class PromptRenderResult:
    """
    Prompt 渲染结果。

    system_prompt：真正发送给模型的 system prompt
    version：当前 prompt 版本
    template_name：模板名称
    variables：本次渲染用到的变量
    """

    system_prompt: str
    version: str
    template_name: str
    variables: dict[str, Any]

    @property
    def preview(self) -> str:
        return self.system_prompt[:300]


def get_available_chat_prompt_versions() -> list[dict[str, str]]:
    """
    返回当前支持的聊天 Prompt 版本列表。
    """

    return [
        {
            "version": "chat_system_v1",
            "name": "默认实战教练版",
            "description": "偏学习陪练，强调步骤、代码和排查方式。",
        },
        {
            "version": "chat_system_v2",
            "name": "工程化面试表达版",
            "description": "更强调真实项目场景、企业价值和面试表达。",
        },
    ]


def normalize_prompt_version(prompt_version: str | None) -> str:
    """
    如果传入版本不存在，则回退到默认版本。
    """

    if prompt_version and prompt_version in CHAT_PROMPT_TEMPLATES:
        return prompt_version

    return DEFAULT_CHAT_PROMPT_VERSION


def render_chat_system_prompt(
    prompt_version: str | None = None,
    assistant_role: str = "AI 应用开发学习教练",
    learning_stage: str = "Week5：LLM API 工程化",
    answer_language: str = "中文",
    answer_style: str = "简洁、具体、偏实战",
) -> PromptRenderResult:
    """
    根据 prompt_version 渲染聊天场景 system prompt。
    """

    final_version = normalize_prompt_version(prompt_version)
    template = CHAT_PROMPT_TEMPLATES[final_version]

    variables = {
        "assistant_role": assistant_role,
        "learning_stage": learning_stage,
        "answer_language": answer_language,
        "answer_style": answer_style,
    }

    system_prompt = template.format(**variables)

    return PromptRenderResult(
        system_prompt=system_prompt,
        version=final_version,
        template_name=CHAT_PROMPT_TEMPLATE_NAME,
        variables=variables,
    )


def get_chat_prompt_info(prompt_version: str | None = None) -> dict[str, Any]:
    """
    返回指定 Prompt 版本的信息。
    """

    rendered = render_chat_system_prompt(prompt_version=prompt_version)

    return {
        "template_name": rendered.template_name,
        "version": rendered.version,
        "template": CHAT_PROMPT_TEMPLATES[rendered.version],
        "variables": rendered.variables,
        "preview": rendered.preview,
        "available_versions": get_available_chat_prompt_versions(),
        "default_version": DEFAULT_CHAT_PROMPT_VERSION,
    }