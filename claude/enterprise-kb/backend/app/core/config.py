"""
应用配置模块
使用 pydantic-settings 从环境变量读取所有配置，禁止硬编码
"""
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    # LLM 配置
    deepseek_api_key: str = Field(..., env="DEEPSEEK_API_KEY")
    openai_api_key: str = Field("", env="OPENAI_API_KEY")
    embedding_api_key: str = Field(..., env="EMBEDDING_API_KEY")
    embedding_model: str = Field("text-embedding-3-small", env="EMBEDDING_MODEL")
    llm_model: str = Field("deepseek-chat", env="LLM_MODEL")
    llm_base_url: str = Field("https://api.deepseek.com", env="LLM_BASE_URL")

    # 数据库配置
    database_url: str = Field(..., env="DATABASE_URL")

    # JWT 鉴权配置
    jwt_secret: str = Field(..., env="JWT_SECRET")
    jwt_algorithm: str = "HS256"
    access_token_expire_hours: int = 24

    # Langfuse 可观测性配置
    langfuse_public_key: str = Field("", env="LANGFUSE_PUBLIC_KEY")
    langfuse_secret_key: str = Field("", env="LANGFUSE_SECRET_KEY")
    langfuse_host: str = Field("http://langfuse:3000", env="LANGFUSE_HOST")

    # 文档处理配置
    chunk_size: int = Field(500, env="CHUNK_SIZE")
    chunk_overlap: int = Field(50, env="CHUNK_OVERLAP")
    retrieval_top_k: int = Field(5, env="RETRIEVAL_TOP_K")

    # 费用计算（默认 DeepSeek 价格，单位：元/1K tokens）
    token_price_per_1k: float = Field(0.001, env="TOKEN_PRICE_PER_1K")

    # 日志级别
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # 文件上传目录
    upload_dir: str = "/app/uploads"

    class Config:
        env_file = ".env"
        case_sensitive = False


# 全局单例配置对象
settings = Settings()
