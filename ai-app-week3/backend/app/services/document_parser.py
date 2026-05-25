import re
from pathlib import Path
from typing import Dict, List

from pypdf import PdfReader


BASE_DIR = Path(__file__).resolve().parents[2]
SOURCE_DIR = BASE_DIR / "docs" / "source"


def resolve_source_file(filename: str) -> Path:
    normalized = filename.strip().replace("\\", "/")
    target = (SOURCE_DIR / normalized).resolve()
    source_root = SOURCE_DIR.resolve()

    if not str(target).startswith(str(source_root)):
        raise ValueError("非法文件路径。")

    if not target.exists():
        raise FileNotFoundError(f"文件不存在：{normalized}")

    return target


def read_text_with_fallback(path: Path) -> str:
    encodings = ["utf-8", "utf-8-sig", "gbk"]

    for encoding in encodings:
        try:
            return path.read_text(encoding=encoding)
        except UnicodeDecodeError:
            continue

    raise ValueError(f"无法识别文件编码：{path.name}")


def read_source_file(path: Path) -> str:
    suffix = path.suffix.lower()

    if suffix in [".md", ".txt"]:
        text = read_text_with_fallback(path)
    elif suffix == ".pdf":
        reader = PdfReader(str(path))
        parts = []
        for page in reader.pages:
            parts.append(page.extract_text() or "")
        text = "\n".join(parts)
    else:
        raise ValueError("暂只支持 .md / .txt / .pdf 文件。")

    return normalize_text(text)


def normalize_text(text: str) -> str:
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    return text.strip()


def split_text_into_chunks(text: str, chunk_size: int = 500, overlap: int = 100) -> List[Dict]:
    if not text.strip():
        return []

    if chunk_size <= 0:
        raise ValueError("chunk_size 必须大于 0")

    if overlap < 0:
        raise ValueError("overlap 不能小于 0")

    if overlap >= chunk_size:
        raise ValueError("overlap 必须小于 chunk_size")

    chunks = []
    start = 0
    text_len = len(text)

    while start < text_len:
        end = min(start + chunk_size, text_len)
        candidate = text[start:end]

        if end < text_len:
            breakpoints = ["\n\n", "\n", "。", "！", "？", "；", ".", "!", "?", ";", "，", ",", " "]
            for sep in breakpoints:
                pos = candidate.rfind(sep)
                if pos > int(chunk_size * 0.6):
                    end = start + pos + len(sep)
                    candidate = text[start:end]
                    break

        content = candidate.strip()
        if content:
            chunks.append(
                {
                    "chunk_index": len(chunks),
                    "content": content,
                    "char_count": len(content),
                    "meta": {
                        "start": start,
                        "end": end,
                    },
                }
            )

        if end >= text_len:
            break

        start = max(end - overlap, start + 1)

    return chunks