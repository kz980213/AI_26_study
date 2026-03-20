from app.logger import get_logger
##argparse 是专门用来做命令行参数解析的。
import argparse

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
    message = f"Hello, {name}!"
    logger.info('CLI started')
    logger.info(message)
    return message

def main() -> None:
    parser = build_parse() 
    ##解析命令行参数
    args = parser.parse_args()
    run(args.name)
