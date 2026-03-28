from app.logger import get_logger
##argparse 是专门用来做命令行参数解析的。
import argparse

from app.services.greeting import build_greeting
from app.exceptions import InvalidNameError

##字符串序列  一个有顺序、可以按索引访问的序列类型，如list、tuple、str等
from collections.abc import Sequence 

from typing import Optional

logger = get_logger()

def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="AI App CLI")
    parser.add_argument(
        "--name",
        default="AI App",
        help="Name to greet"
    )
    return parser


def run(name: str) -> str:
    message = build_greeting(name)
    logger.info('CLI started')
    logger.info(message)
    return message

def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_parser()
    ##解析命令行参数
    args = parser.parse_args(argv)
    try:
        run(args.name)
        return 0
    except InvalidNameError as e:
        logger.error(f"Error: {e}")
        return 1
