from __future__ import annotations

import logging
from functools import lru_cache
from typing import Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """全局配置，从环境变量读取，禁止硬编码"""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    # --- LLM 配置 ---
    deepseek_api_key: str = "your_deepseek_key"
    openai_api_key: str = "your_openai_key"
    llm_model: str = "deepseek-chat"
    llm_base_url: str = "https://api.deepseek.com"

    # --- Embedding 配置 ---
    embedding_api_key: str = "your_embedding_key"
    embedding_model: str = "text-embedding-3-small"
    embedding_base_url: str = "https://api.openai.com/v1"

    # --- 数据库 ---
    database_url: str = "postgresql+asyncpg://kb_user:kb_pass@localhost:5432/kb_db"

    # --- JWT ---
    jwt_secret: str = "change_this_to_a_random_string"
    jwt_algorithm: str = "HS256"
    jwt_expire_hours: int = 24

    # --- Langfuse ---
    langfuse_public_key: Optional[str] = None
    langfuse_secret_key: Optional[str] = None
    langfuse_host: str = "http://localhost:3000"

    # --- Chunk 参数 ---
    chunk_size: int = Field(default=500, ge=100, le=2000)
    chunk_overlap: int = Field(default=50, ge=0, le=500)

    # --- 检索参数 ---
    retrieval_top_k: int = Field(default=5, ge=1, le=50)
    retrieval_score_threshold: float = Field(default=0.3, ge=0.0, le=1.0)

    # --- 费用计算 ---
    token_price_per_1k: float = Field(default=0.001, ge=0.0)

    # --- 日志级别 ---
    log_level: str = "INFO"

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        valid = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        v = v.upper()
        if v not in valid:
            raise ValueError(f"log_level 必须是 {valid} 之一，当前: {v}")
        return v


@lru_cache
def get_settings() -> Settings:
    return Settings()


def setup_logging() -> None:
    """配置 structlog JSON 格式日志"""
    settings = get_settings()
    logging.basicConfig(
        format='{"time":"%(asctime)s","level":"%(levelname)s","msg":"%(message)s"}',
        level=getattr(logging, settings.log_level, logging.INFO),
    )
