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