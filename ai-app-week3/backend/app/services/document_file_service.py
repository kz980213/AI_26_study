from pathlib import Path
from typing import Tuple

from fastapi import UploadFile


ALLOWED_TEXT_FILE_EXTENSIONS = {".txt", ".md", ".markdown"}

MAX_TEXT_FILE_SIZE = 1024 * 1024  # 1MB，今天先限制小一点，避免误传大文件


class DocumentFileError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


def validate_text_filename(filename: str) -> None:
    if not filename:
        raise DocumentFileError("文件名不能为空")

    suffix = Path(filename).suffix.lower()

    if suffix not in ALLOWED_TEXT_FILE_EXTENSIONS:
        raise DocumentFileError(
            "当前只支持 .txt / .md / .markdown 文件"
        )


def decode_text_file(raw_bytes: bytes) -> str:
    """
    尝试用常见编码解码文本文件。

    优先级：
    1. utf-8-sig：兼容带 BOM 的 UTF-8
    2. utf-8
    3. gbk：兼容部分 Windows 中文文本
    """
    encodings = ["utf-8-sig", "utf-8", "gbk"]

    for encoding in encodings:
        try:
            return raw_bytes.decode(encoding)
        except UnicodeDecodeError:
            continue

    raise DocumentFileError(
        "文件解码失败，请确认文件是 UTF-8 或 GBK 编码的文本文件"
    )


async def read_uploaded_text_file(file: UploadFile) -> Tuple[str, str]:
    """
    返回：
    (filename, text_content)
    """
    filename = file.filename or ""

    validate_text_filename(filename)

    raw_bytes = await file.read()

    if not raw_bytes:
        raise DocumentFileError("上传文件内容为空")

    if len(raw_bytes) > MAX_TEXT_FILE_SIZE:
        raise DocumentFileError("文件过大，当前最大支持 1MB")

    text = decode_text_file(raw_bytes).strip()

    if not text:
        raise DocumentFileError("文件解析后内容为空")

    if len(text) < 10:
        raise DocumentFileError("文件内容太短，至少需要 10 个字符")

    return filename, text