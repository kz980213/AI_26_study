/** SSE client 封装：连接后端流式问答接口 */

export interface CitationItem {
  chunk_id: string
  content: string
  metadata: Record<string, unknown>
  score: number
}

export interface SSECallbacks {
  onToken: (content: string) => void
  onDone: (citations: CitationItem[]) => void
  onError: (message: string) => void
}

const API_BASE = '/api'

export async function streamChat(
  question: string,
  token: string,
  sessionId: string | null,
  fileFilter: string | null,
  callbacks: SSECallbacks,
): Promise<void> {
  const params = new URLSearchParams({ question, token })
  if (sessionId) params.set('session_id', sessionId)
  if (fileFilter) params.set('file_filter', fileFilter)

  const url = `${API_BASE}/chat/stream?${params.toString()}`

  const response = await fetch(url, {
    method: 'GET',
    headers: { Accept: 'text/event-stream' },
  })

  if (!response.ok) {
    const errData = await response.json().catch(() => ({}))
    callbacks.onError((errData as Record<string, string>).detail || `请求失败: ${response.status}`)
    return
  }

  const reader = response.body?.getReader()
  if (!reader) {
    callbacks.onError('无法读取响应流')
    return
  }

  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const lines = buffer.split('\n')
    buffer = lines.pop() || ''

    for (const line of lines) {
      if (!line.startsWith('data: ')) continue
      const dataStr = line.slice(6).trim()
      if (!dataStr || dataStr === '[DONE]') continue

      try {
        const event = JSON.parse(dataStr)
        if (event.type === 'token') {
          callbacks.onToken(event.content)
        } else if (event.type === 'done') {
          callbacks.onDone(event.citations || [])
        } else if (event.type === 'error') {
          callbacks.onError(event.message)
        }
      } catch {
        // 忽略解析失败的单行
      }
    }
  }
}
