import { API_BASE_URL } from './http'
import { getToken } from '../utils/storage'

type StreamHandlers = {
  onStart?: (payload: any) => void
  onChunk?: (payload: any) => void
  onUsage?: (payload: any) => void
  onDone?: (payload: any) => void
  onError?: (payload: any) => void
}

export async function streamChatApi(
  message: string,
  handlers: StreamHandlers
) {
  const token = getToken()

  const response = await fetch(`${API_BASE_URL}/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
    body: JSON.stringify({ message }),
  })

  if (!response.ok) {
    let errorText = '请求失败'
    try {
      errorText = await response.text()
    } catch {
      // ignore
    }
    throw new Error(`HTTP ${response.status} - ${errorText}`)
  }

  if (!response.body) {
    throw new Error('当前浏览器不支持流式读取 response.body')
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder('utf-8')
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()

    if (done) {
      break
    }

    buffer += decoder.decode(value, { stream: true })

    const blocks = buffer.split('\n\n')
    buffer = blocks.pop() || ''

    for (const block of blocks) {
      const lines = block.split('\n')

      for (const line of lines) {
        const trimmed = line.trim()

        if (!trimmed) continue
        if (trimmed.startsWith(':')) continue
        if (!trimmed.startsWith('data:')) continue

        const raw = trimmed.slice(5).trim()
        if (!raw) continue

        const payload = JSON.parse(raw)

        switch (payload.type) {
          case 'start':
            handlers.onStart?.(payload)
            break
          case 'chunk':
            handlers.onChunk?.(payload)
            break
          case 'usage':
            handlers.onUsage?.(payload)
            break
          case 'done':
            handlers.onDone?.(payload)
            break
          case 'error':
            handlers.onError?.(payload)
            break
          default:
            break
        }
      }
    }
  }
}