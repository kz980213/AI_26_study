import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-key")
    ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "60"))
    DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app.db")
    CORS_ALLOW_ORIGINS = os.getenv(
        "CORS_ALLOW_ORIGINS",
        "http://localhost:5173,http://127.0.0.1:5173,http://localhost:5180,http://127.0.0.1:5180",
    ).split(",")
    
    DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_API_URL = os.getenv(
        "DEEPSEEK_API_URL",
        "https://api.deepseek.com/chat/completions"
    )
    DEEPSEEK_MODEL = os.getenv("DEEPSEEK_MODEL", "deepseek-chat")
    DEEPSEEK_TIMEOUT_SECONDS: int = 60
    DEEPSEEK_INPUT_PRICE_CNY_PER_1M_TOKENS: float = 0
    DEEPSEEK_OUTPUT_PRICE_CNY_PER_1M_TOKENS: float = 0


settings = Settings()