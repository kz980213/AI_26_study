from typing import List, Tuple


def normalize_text(text: str) -> str:
    """
    做最小文本清洗：
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

    注意：
    char_end 是 Python 切片意义上的结束位置，不包含该位置。
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