import logging
from app.config import get_settings

def get_logger(name: str = 'ai_app') -> logging.Logger:
    settings = get_settings()
    logging_name = name or settings.app_name
    logger = logging.getLogger(logging_name)
    if not logger.handlers:
        level_name = settings.log_level.upper()
        level = getattr(logging, level_name, logging.INFO)
        logger.setLevel(level)

        handler = logging.StreamHandler()
        formatter = logging.Formatter(
            '[%(asctime)s] [%(levelname)s] %(name)s: %(message)s'
            )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger