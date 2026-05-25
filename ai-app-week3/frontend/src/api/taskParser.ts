import http from './http'

export function parseTaskApi(text: string) {
  return http.post('/ai-tasks/parse', { text })
}

export function getTaskRecordsApi(limit = 10) {
  return http.get('/ai-tasks/records', {
    params: { limit },
  })
}