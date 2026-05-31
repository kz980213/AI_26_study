from sqlalchemy import inspect, text

from app.database import engine


def ensure_llm_call_log_prompt_columns() -> None:
    """
    给已存在的 llm_call_logs 表补充 Prompt 相关字段。

    注意：
    - Base.metadata.create_all 只会创建不存在的表
    - 不会自动修改已存在的表结构
    - 所以开发阶段用这个小迁移函数补字段
    """

    inspector = inspect(engine)

    table_names = inspector.get_table_names()

    if "llm_call_logs" not in table_names:
        return

    columns = inspector.get_columns("llm_call_logs")
    existing_column_names = {column["name"] for column in columns}

    alter_sql_list: list[str] = []

    if "prompt_template_name" not in existing_column_names:
        alter_sql_list.append(
            "ALTER TABLE llm_call_logs ADD COLUMN prompt_template_name VARCHAR(100)"
        )

    if "prompt_version" not in existing_column_names:
        alter_sql_list.append(
            "ALTER TABLE llm_call_logs ADD COLUMN prompt_version VARCHAR(100)"
        )

    if "system_prompt_preview" not in existing_column_names:
        alter_sql_list.append(
            "ALTER TABLE llm_call_logs ADD COLUMN system_prompt_preview TEXT"
        )

    if not alter_sql_list:
        return

    with engine.begin() as connection:
        for sql in alter_sql_list:
            connection.execute(text(sql))