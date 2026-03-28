"""retriever 单元测试"""
from __future__ import annotations

import asyncio
import json
import os
import sys
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


class TestVectorSearch:
    """向量搜索单元测试"""

    @pytest.mark.asyncio
    async def test_vector_search_returns_results(self):
        """测试向量检索返回结果"""
        from app.services.retriever import vector_search

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_row = MagicMock()
        mock_row.id = "test-chunk-id"
        mock_row.content = "这是一个测试文档片段"
        mock_row.metadata = json.dumps({
            "file_name": "test.pdf",
            "page_num": 1,
            "chunk_index": 0,
        })
        mock_row.chunk_index = 0
        mock_row.page_num = 1
        mock_row.file_name = "test.pdf"
        mock_row.score = 0.95
        mock_result.fetchall.return_value = [mock_row]
        mock_db.execute = AsyncMock(return_value=mock_result)

        query_embedding = [0.1] * 1536
        results = await vector_search(
            mock_db, query_embedding, top_k=5, score_threshold=0.3
        )

        assert len(results) == 1
        assert results[0]["content"] == "这是一个测试文档片段"
        assert results[0]["score"] == 0.95
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_vector_search_with_file_filter(self):
        """测试文件名过滤"""
        from app.services.retriever import vector_search

        mock_db = AsyncMock()
        mock_result = MagicMock()
        mock_result.fetchall.return_value = []
        mock_db.execute = AsyncMock(return_value=mock_result)

        query_embedding = [0.1] * 1536
        results = await vector_search(
            mock_db,
            query_embedding,
            top_k=5,
            file_filter="specific.pdf",
        )

        assert len(results) == 0
        call_args = mock_db.execute.call_args
        sql_text = str(call_args[0][0].text)
        assert "file_name" in sql_text


class TestQueryEmbedding:
    """查询 embedding 单元测试"""

    @pytest.mark.asyncio
    async def test_get_query_embedding(self):
        """测试查询 embedding 调用"""
        from app.services.retriever import _get_query_embedding

        mock_response = MagicMock()
        mock_response.json.return_value = {
            "data": [{"index": 0, "embedding": [0.1] * 1536}]
        }
        mock_response.raise_for_status = MagicMock()

        with patch("app.services.retriever.httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__ = AsyncMock(return_value=AsyncMock(
                post=AsyncMock(return_value=mock_response)
            ))
            mock_client.return_value.__aexit__ = AsyncMock(return_value=False)

            result = await _get_query_embedding("测试问题")

            assert len(result) == 1536
            assert isinstance(result, list)


class TestParseCitations:
    """引用解析单元测试"""

    def test_parse_citations_basic(self):
        """测试基本引用解析"""
        from app.services.generator import _parse_citations
        from app.models.schemas import ChunkResult
        from uuid import uuid4

        chunks = [
            ChunkResult(
                chunk_id=uuid4(),
                content="这是第一个文档片段",
                metadata={"file_name": "doc1.pdf"},
                score=0.9,
                file_name="doc1.pdf",
                page_num=1,
            ),
            ChunkResult(
                chunk_id=uuid4(),
                content="这是第二个文档片段",
                metadata={"file_name": "doc2.pdf"},
                score=0.8,
                file_name="doc2.pdf",
                page_num=2,
            ),
        ]

        answer = "根据文档[1]和[2]的内容，答案是..."
        citations = _parse_citations(answer, chunks)

        assert len(citations) == 2
        assert citations[0].content == "这是第一个文档片段"

    def test_parse_citations_no_match(self):
        """测试无引用的情况"""
        from app.services.generator import _parse_citations
        from app.models.schemas import ChunkResult
        from uuid import uuid4

        chunks = [
            ChunkResult(
                chunk_id=uuid4(),
                content="测试内容",
                metadata={},
                score=0.9,
                file_name="test.pdf",
            ),
        ]

        answer = "这个回答没有任何引用标注"
        citations = _parse_citations(answer, chunks)

        assert len(citations) == 0
