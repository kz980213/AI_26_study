from typing import Any, Dict, List

from app.schemas import ToolDefinitionItem


TOOL_REGISTRY: Dict[str, Dict[str, Any]] = {
    "create_task": {
        "description": "创建一条结构化任务记录。当用户想创建、添加、安排、提醒一个任务时使用。",
        "arguments_schema": {
            "title": {
                "type": "string",
                "required": True,
                "description": "任务标题，简短明确",
            },
            "category": {
                "type": "string",
                "required": True,
                "description": "任务分类，例如 学习 / 工作 / 生活 / 其他",
            },
            "priority": {
                "type": "string",
                "required": True,
                "enum": ["low", "medium", "high"],
                "description": "任务优先级",
            },
            "due_time": {
                "type": "string | null",
                "required": False,
                "description": "截止时间或提醒时间，没有则为 null",
            },
            "description": {
                "type": "string | null",
                "required": False,
                "description": "任务描述，没有则为 null",
            },
        },
    },
    "list_recent_tasks": {
        "description": "查看最近的结构化任务记录。当用户想查看、列出、查询最近任务时使用。",
        "arguments_schema": {
            "limit": {
                "type": "integer",
                "required": False,
                "minimum": 1,
                "maximum": 20,
                "default": 5,
                "description": "返回最近多少条任务",
            },
        },
    },
}


def list_available_tools() -> List[ToolDefinitionItem]:
    return [
        ToolDefinitionItem(
            name=name,
            description=config["description"],
            arguments_schema=config["arguments_schema"],
        )
        for name, config in TOOL_REGISTRY.items()
    ]


def is_allowed_tool_name(tool_name: str) -> bool:
    return tool_name in TOOL_REGISTRY


def ensure_allowed_tool_name(tool_name: str) -> None:
    if not is_allowed_tool_name(tool_name):
        allowed_names = ", ".join(TOOL_REGISTRY.keys())
        raise ValueError(
            f"不允许调用工具：{tool_name}。当前允许的工具只有：{allowed_names}"
        )