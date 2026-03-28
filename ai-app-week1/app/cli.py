from app.logger import get_logger
##argparse 是专门用来做命令行参数解析的。
import argparse

from app.services.greeting import build_greeting
from app.exceptions import InvalidNameError

logger = get_logger()

def build_parse() -> argparse.ArgumentParser:
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

def main() -> None:
    parser = build_parse()
    ##解析命令行参数
    args = parser.parse_args()
    try:
        run(args.name)
    except InvalidNameError as e:
        logger.error(f"Error: {e}")
        ##让程序退出，并返回退出码 1。0 通常表示成功，非 0 通常表示失败
        raise SystemExit(1)
