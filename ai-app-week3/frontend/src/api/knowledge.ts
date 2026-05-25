import http from './http'

export function ingestKnowledgeApi(payload: {
  filename: string
  chunk_size: number
  overlap: number
}) {
  return http.post('/knowledge/ingest', payload)
}

export function getKnowledgeDocumentsApi(limit = 10) {
  return http.get('/knowledge/documents', {
    params: { limit },
  })
}

export function getKnowledgeChunksApi(documentId: number, limit = 20) {
  return http.get('/knowledge/chunks', {
    params: {
      document_id: documentId,
      limit,
    },
  })
}