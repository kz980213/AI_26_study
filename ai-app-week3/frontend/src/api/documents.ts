export interface DocumentItem {
  id: number
  title: string
  source_type: string
  chunk_size: number
  chunk_overlap: number
  chunk_count: number
  created_at: string
}

export interface DocumentChunkItem {
  id: number
  document_id: number
  chunk_index: number
  content: string
  char_start: number
  char_end: number
  is_active: boolean
  quality_status: ChunkQualityStatus
  quality_note?: string | null
  created_at: string
  updated_at?: string | null
}

export interface DocumentIngestTextResponse {
  success: boolean
  document: DocumentItem
  chunks: DocumentChunkItem[]
}

export interface DocumentChunkSearchItem {
  id: number
  document_id: number
  document_title: string
  chunk_index: number
  content: string
  char_start: number
  char_end: number
  is_active: boolean
  quality_status: ChunkQualityStatus
  quality_note?: string | null
  created_at: string
}

export interface DocumentStatsResponse {
  total_documents: number
  total_chunks: number
  active_chunks: number
  inactive_chunks: number
  quality_counts: Record<string, number>
  average_chunks_per_document: number
  latest_document?: DocumentItem | null
}

export type SplitStrategy = 'chars' | 'markdown_headings'

export type ChunkQualityStatus =
  | 'unknown'
  | 'good'
  | 'needs_review'
  | 'bad'

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export async function ingestTextDocument(payload: {
  title: string
  content: string
  chunk_size: number
  chunk_overlap: number
  split_strategy: SplitStrategy
}): Promise<DocumentIngestTextResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/documents/ingest-text`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '文档解析与切分失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result
}

export async function fetchRecentDocuments(
  limit = 20
): Promise<DocumentItem[]> {
  const response = await fetch(
    `${API_BASE_URL}/ai/documents/recent?limit=${limit}`
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取最近文档失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.items || []
}

export async function fetchDocumentChunks(
  documentId: number
): Promise<DocumentChunkItem[]> {
  const response = await fetch(
    `${API_BASE_URL}/ai/documents/${documentId}/chunks`
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取文档 chunks 失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.items || []
}

export async function rechunkDocument(
  documentId: number,
  payload: {
    chunk_size: number
    chunk_overlap: number
    split_strategy: SplitStrategy
  }
): Promise<DocumentIngestTextResponse> {
  const response = await fetch(
    `${API_BASE_URL}/ai/documents/${documentId}/rechunk`,
    {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '重新切分文档失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result
}

export async function uploadTextDocument(payload: {
  file: File
  title?: string
  chunk_size: number
  chunk_overlap: number
  split_strategy: SplitStrategy
}): Promise<DocumentIngestTextResponse> {
  const formData = new FormData()

  formData.append('file', payload.file)

  if (payload.title) {
    formData.append('title', payload.title)
  }

  formData.append('chunk_size', String(payload.chunk_size))
  formData.append('chunk_overlap', String(payload.chunk_overlap))
  formData.append('split_strategy', payload.split_strategy)

  const response = await fetch(`${API_BASE_URL}/ai/documents/upload-text`, {
    method: 'POST',
    body: formData,
  })

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '上传文档失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result
}

export async function searchDocumentChunks(payload: {
  keyword: string
  document_id?: number | null
  limit?: number
}): Promise<DocumentChunkSearchItem[]> {
  const params = new URLSearchParams()

  params.set('keyword', payload.keyword)

  if (payload.document_id) {
    params.set('document_id', String(payload.document_id))
  }

  params.set('limit', String(payload.limit || 20))

  const response = await fetch(
    `${API_BASE_URL}/ai/documents/chunks/search?${params.toString()}`
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '搜索 chunks 失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.items || []
}

export async function updateDocumentChunk(
  chunkId: number,
  payload: {
    content: string
    is_active: boolean
    quality_status: ChunkQualityStatus
    quality_note?: string | null
  }
): Promise<DocumentChunkItem> {
  const response = await fetch(
    `${API_BASE_URL}/ai/documents/chunks/${chunkId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '更新 chunk 失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.item
}

export async function fetchDocumentDetail(
  documentId: number
): Promise<DocumentItem> {
  const response = await fetch(`${API_BASE_URL}/ai/documents/${documentId}`)

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取文档详情失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.item
}

export async function fetchDocumentStats(): Promise<DocumentStatsResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/documents/stats`)

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取文档统计失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result
}