import hashlib
import math


class EmbeddingService:
    """
    Week8 Day01 的本地 embedding 服务。

    说明：
    - 这里不是最终生产方案
    - 目的是先跑通：文本 -> 向量 -> 入库
    - 后面可以替换为真实 embedding API 或本地模型
    """

    def __init__(self, dimension: int = 32):
        self.dimension = dimension
        self.provider = "local"
        self.model = "mock-hash-embedding-v1"

    def embed_text(self, text: str) -> list[float]:
        if not text or not text.strip():
            raise ValueError("text 不能为空")

        vector = [0.0 for _ in range(self.dimension)]

        words = list(text.strip())

        for word in words:
            digest = hashlib.md5(word.encode("utf-8")).hexdigest()
            index = int(digest[:8], 16) % self.dimension
            value = (int(digest[8:16], 16) % 1000) / 1000.0
            vector[index] += value

        return self._normalize(vector)

    def _normalize(self, vector: list[float]) -> list[float]:
        norm = math.sqrt(sum(x * x for x in vector))

        if norm == 0:
            return vector

        return [round(x / norm, 6) for x in vector]