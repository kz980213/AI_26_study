import logging
from pathlib import Path
from app.config import get_settings
from typing import Optional


def get_logger(name: Optional[str] = None) -> logging.Logger:
    settings = get_settings()
    logger_name = name or settings.app_name
    logger = logging.getLogger(logger_name)

    if logger.handlers:
        return logger

    level_name = settings.log_level.upper()
    level = getattr(logging, level_name, logging.INFO)
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] %(name)s: %(message)s"
    )

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)

    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    file_handler = logging.FileHandler(log_dir / "app.log", encoding="utf-8")
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)

    return logger