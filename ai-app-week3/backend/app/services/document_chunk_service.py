import re
from typing import List, Tuple


def normalize_text(text: str) -> str:
    """
    最小文本清洗：
    - 统一换行
    - 去掉首尾空白
    - 保留段落结构
    """
    return text.replace("\r\n", "\n").replace("\r", "\n").strip()


def split_text_by_chars(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Tuple[str, int, int]]:
    """
    按字符长度切分文本。
    返回：
    [
      (chunk_content, char_start, char_end)
    ]
    """
    normalized = normalize_text(text)

    if not normalized:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")

    chunks: List[Tuple[str, int, int]] = []

    start = 0
    text_length = len(normalized)

    while start < text_length:
        end = min(start + chunk_size, text_length)
        chunk_content = normalized[start:end].strip()

        if chunk_content:
            chunks.append((chunk_content, start, end))

        if end >= text_length:
            break

        start = end - chunk_overlap

    return chunks


def split_markdown_by_headings(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
) -> List[Tuple[str, int, int]]:
    """
    按 Markdown 标题切分。

    基本策略：
    1. 识别 # / ## / ### 开头的标题行
    2. 每个标题段落作为一个候选 section
    3. 如果 section 太长，再退回按字符切分
    4. 如果没有标题，则退回按字符切分
    """
    normalized = normalize_text(text)

    if not normalized:
        return []

    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap 必须小于 chunk_size")

    heading_pattern = re.compile(r"(?m)^#{1,6}\s+.+$")

    matches = list(heading_pattern.finditer(normalized))

    if not matches:
        return split_text_by_chars(
            text=normalized,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    chunks: List[Tuple[str, int, int]] = []

    for index, match in enumerate(matches):
        section_start = match.start()

        if index + 1 < len(matches):
            section_end = matches[index + 1].start()
        else:
            section_end = len(normalized)

        section_text = normalized[section_start:section_end].strip()

        if not section_text:
            continue

        if len(section_text) <= chunk_size:
            chunks.append((section_text, section_start, section_end))
            continue

        # section 太长时，退回按字符切分
        sub_chunks = split_text_by_chars(
            text=section_text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

        for sub_content, sub_start, sub_end in sub_chunks:
            chunks.append(
                (
                    sub_content,
                    section_start + sub_start,
                    section_start + sub_end,
                )
            )

    return chunks


def split_text(
    text: str,
    chunk_size: int = 500,
    chunk_overlap: int = 50,
    split_strategy: str = "chars",
) -> List[Tuple[str, int, int]]:
    """
    统一切分入口。
    """
    if split_strategy == "markdown_headings":
        return split_markdown_by_headings(
            text=text,
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
        )

    return split_text_by_chars(
        text=text,
        chunk_size=chunk_size,
        chunk_overlap=chunk_overlap,
    )