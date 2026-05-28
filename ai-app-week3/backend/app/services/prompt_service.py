from dataclasses import dataclass
from typing import Any


CHAT_PROMPT_TEMPLATE_NAME = "default_chat_system_prompt"
CHAT_PROMPT_VERSION = "chat_system_v1"


CHAT_SYSTEM_PROMPT_TEMPLATE = """
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
""".strip()


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
        """
        给前端或日志展示的简短预览。
        """

        return self.system_prompt[:300]


def render_chat_system_prompt(
    assistant_role: str = "AI 应用开发学习教练",
    learning_stage: str = "Week5：LLM API 工程化",
    answer_language: str = "中文",
    answer_style: str = "简洁、具体、偏实战",
) -> PromptRenderResult:
    """
    渲染聊天场景 system prompt。

    后续如果要做多版本 Prompt，可以从这里扩展：
    - chat_system_v1
    - chat_system_v2
    - rag_answer_v1
    - json_extract_v1
    """

    variables = {
        "assistant_role": assistant_role,
        "learning_stage": learning_stage,
        "answer_language": answer_language,
        "answer_style": answer_style,
    }

    system_prompt = CHAT_SYSTEM_PROMPT_TEMPLATE.format(**variables)

    return PromptRenderResult(
        system_prompt=system_prompt,
        version=CHAT_PROMPT_VERSION,
        template_name=CHAT_PROMPT_TEMPLATE_NAME,
        variables=variables,
    )


def get_chat_prompt_info() -> dict[str, Any]:
    """
    返回当前聊天 Prompt 模板信息。

    用于前端展示或调试。
    """

    rendered = render_chat_system_prompt()

    return {
        "template_name": rendered.template_name,
        "version": rendered.version,
        "template": CHAT_SYSTEM_PROMPT_TEMPLATE,
        "variables": rendered.variables,
        "preview": rendered.preview,
    }