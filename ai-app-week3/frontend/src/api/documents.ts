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
  created_at: string
}

export interface DocumentIngestTextResponse {
  success: boolean
  document: DocumentItem
  chunks: DocumentChunkItem[]
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export async function ingestTextDocument(payload: {
  title: string
  content: string
  chunk_size: number
  chunk_overlap: number
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