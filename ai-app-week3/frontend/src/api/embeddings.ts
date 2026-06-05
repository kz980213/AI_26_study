const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8010";

export interface ChunkEmbeddingResponse {
  id: number;
  chunk_id: number;
  provider: string;
  model: string;
  dimension: number;
  embedding: number[];
  status: string;
  error_message?: string | null;
  created_at: string;
  updated_at: string;
}

async function parseError(response: Response, fallbackMessage: string) {
  try {
    const data = await response.json();
    return data?.detail || fallbackMessage;
  } catch {
    return fallbackMessage;
  }
}

export async function createChunkEmbedding(
  chunkId: number
): Promise<ChunkEmbeddingResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/chunks/${chunkId}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `创建 chunk embedding 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export async function getChunkEmbedding(
  chunkId: number
): Promise<ChunkEmbeddingResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/chunks/${chunkId}`,
    {
      method: "GET",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `获取 chunk embedding 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export interface BatchEmbeddingItem {
  chunk_id: number;
  status: "success" | "skipped" | "failed";
  message: string;
  embedding_id?: number | null;
  dimension?: number;
}

export interface BatchDocumentEmbeddingResponse {
  document_id: number;
  total_active_chunks: number;
  success_count: number;
  skipped_count: number;
  failed_count: number;
  items: BatchEmbeddingItem[];
}

export async function createDocumentChunkEmbeddings(
  documentId: number,
  skipExisting = true
): Promise<BatchDocumentEmbeddingResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/documents/${documentId}/chunks?skip_existing=${skipExisting}`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `批量创建文档 embeddings 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export interface EmbeddingSearchRequest {
  query: string;
  top_k: number;
  document_id?: number | null;
  only_active: boolean;
  quality_status?: string | null;
  score_threshold?: number | null;
}

export interface EmbeddingSearchResultItem {
  chunk_id: number;
  document_id?: number | null;
  embedding_id: number;
  score: number;
  content: string;
  content_preview: string;
  provider: string;
  model: string;
  dimension: number;
  is_active?: boolean | null;
  status?: string | null;
  quality_status?: string | null;
  quality_note?: string | null;
  error_message?: string;
}

export interface EmbeddingSearchResponse {
  query: string;
  top_k: number;
  document_id?: number | null;
  only_active: boolean;
  quality_status?: string | null;
  score_threshold?: number | null;
  applied_filters: {
    document_id?: number | null;
    only_active: boolean;
    quality_status?: string | null;
    score_threshold?: number | null;
  };
  total_candidates: number;
  returned_count: number;
  matched_after_score_filter: number;
  max_score?: number | null;
  min_score?: number | null;
  results: EmbeddingSearchResultItem[];
  log_id?: number;
  elapsed_ms?: number;
} 

export async function searchChunkEmbeddings(
  payload: EmbeddingSearchRequest
): Promise<EmbeddingSearchResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/embeddings/search`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payload),
  });

  if (!response.ok) {
    const message = await parseError(
      response,
      `向量检索失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export interface EmbeddingSearchLogItem {
  id: number;
  query: string;
  top_k: number;
  document_id?: number | null;
  only_active: boolean;
  quality_status?: string | null;
  score_threshold?: number | null;
  total_candidates: number;
  matched_after_score_filter: number;
  returned_count: number;
  max_score?: number | null;
  min_score?: number | null;
  result_chunk_ids: number[];
  elapsed_ms: number;
  created_at: string;
}

export interface RecentEmbeddingSearchLogsResponse {
  items: EmbeddingSearchLogItem[];
}

export async function getRecentEmbeddingSearchLogs(
  limit = 20
): Promise<RecentEmbeddingSearchLogsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/search-logs/recent?limit=${limit}`,
    {
      method: "GET",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `获取检索日志失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export interface EmbeddingDocumentCoverageItem {
  document_id: number;
  title: string;
  total_chunks: number;
  active_chunks: number;
  embedded_active_chunks: number;
  missing_active_chunks: number;
  coverage_rate: number;
}

export interface EmbeddingStatsResponse {
  total_documents: number;
  total_chunks: number;
  active_chunks: number;
  embedding_records: number;
  embedded_active_chunks: number;
  missing_active_chunks: number;
  coverage_rate: number;
  documents: EmbeddingDocumentCoverageItem[];
}

export interface MissingEmbeddingChunkItem {
  chunk_id: number;
  document_id?: number | null;
  content_preview: string;
  quality_status?: string | null;
  quality_note?: string | null;
  is_active?: boolean | null;
  status?: string | null;
}

export interface MissingEmbeddingChunksResponse {
  document_id?: number | null;
  limit: number;
  missing_count: number;
  items: MissingEmbeddingChunkItem[];
}

export async function getEmbeddingStats(): Promise<EmbeddingStatsResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/embeddings/stats`, {
    method: "GET",
  });

  if (!response.ok) {
    const message = await parseError(
      response,
      `获取 embedding 覆盖率统计失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export async function getMissingEmbeddingChunks(
  documentId?: number | null,
  limit = 50
): Promise<MissingEmbeddingChunksResponse> {
  const params = new URLSearchParams();

  params.set("limit", String(limit));

  if (documentId) {
    params.set("document_id", String(documentId));
  }

  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/missing-chunks?${params.toString()}`,
    {
      method: "GET",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `获取缺失 embedding chunks 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export interface DeleteChunkEmbeddingResponse {
  chunk_id: number;
  deleted: boolean;
  embedding_id?: number | null;
  message: string;
}

export interface RebuildChunkEmbeddingResponse {
  chunk_id: number;
  deleted_before_rebuild: boolean;
  embedding_id: number;
  provider: string;
  model: string;
  dimension: number;
  status: string;
  message: string;
}

export interface RebuildDocumentEmbeddingsResponse {
  document_id: number;
  total_active_chunks: number;
  success_count: number;
  skipped_count: number;
  failed_count: number;
  mode: string;
  message: string;
  items: BatchEmbeddingItem[];
}

export interface RagReadinessCheckItem {
  key: string;
  label: string;
  passed: boolean;
  message: string;
}

export interface RagReadinessResponse {
  ready_for_rag: boolean;
  checks: RagReadinessCheckItem[];
  suggestions: string[];
  stats: EmbeddingStatsResponse;
}

export async function deleteChunkEmbedding(
  chunkId: number
): Promise<DeleteChunkEmbeddingResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/chunks/${chunkId}`,
    {
      method: "DELETE",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `删除 chunk embedding 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export async function rebuildChunkEmbedding(
  chunkId: number
): Promise<RebuildChunkEmbeddingResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/chunks/${chunkId}/rebuild`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `重建 chunk embedding 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export async function rebuildDocumentEmbeddings(
  documentId: number
): Promise<RebuildDocumentEmbeddingsResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/documents/${documentId}/rebuild`,
    {
      method: "POST",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `重建文档 embeddings 失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}

export async function getRagReadiness(): Promise<RagReadinessResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/embeddings/rag-readiness`,
    {
      method: "GET",
    }
  );

  if (!response.ok) {
    const message = await parseError(
      response,
      `获取 RAG 准备状态失败：${response.status}`
    );
    throw new Error(message);
  }

  return response.json();
}