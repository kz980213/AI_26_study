export interface ChatStreamPayload {
  type: 'start' | 'chunk' | 'done' | 'error' | 'heartbeat'
  message?: string
  content?: string
  index?: number
  conversation_id?: string
}

export interface CreateChatStreamOptions {
  message: string
  conversationId?: string
  endpoint?: string
  timeoutMs?: number
  onOpen?: () => void
  onStart?: (data: ChatStreamPayload) => void
  onChunk?: (data: ChatStreamPayload) => void
  onDone?: (data: ChatStreamPayload) => void
  onServerError?: (data: ChatStreamPayload) => void
  onConnectionError?: () => void
}

export interface ChatStreamController {
  close: () => void
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

function parseMessageEvent(event: Event): ChatStreamPayload {
  const messageEvent = event as MessageEvent
  return JSON.parse(messageEvent.data) as ChatStreamPayload
}

export function createChatStream(options: CreateChatStreamOptions): ChatStreamController {
  const {
    message,
    conversationId,
    endpoint = '/ai/chat/stream',
    timeoutMs = 60000,
    onOpen,
    onStart,
    onChunk,
    onDone,
    onServerError,
    onConnectionError,
  } = options

  const params = new URLSearchParams()
  params.set('message', message)

  if (conversationId) {
    params.set('conversation_id', conversationId)
  }

  const url = `${API_BASE_URL}${endpoint}?${params.toString()}`
  const eventSource = new EventSource(url)

  let closed = false
  let timeoutTimer: number | undefined

  function clearStreamTimeout() {
    if (timeoutTimer) {
      window.clearTimeout(timeoutTimer)
      timeoutTimer = undefined
    }
  }

  function close() {
    if (closed) {
      return
    }

    closed = true
    clearStreamTimeout()
    eventSource.close()
  }

  function resetStreamTimeout() {
    clearStreamTimeout()

    timeoutTimer = window.setTimeout(() => {
      if (!closed) {
        close()
        onConnectionError?.()
      }
    }, timeoutMs)
  }

  eventSource.addEventListener('open', () => {
    resetStreamTimeout()
    onOpen?.()
  })

  eventSource.addEventListener('start', (event) => {
    resetStreamTimeout()
    onStart?.(parseMessageEvent(event))
  })

  eventSource.addEventListener('chunk', (event) => {
    resetStreamTimeout()
    onChunk?.(parseMessageEvent(event))
  })

  eventSource.addEventListener('done', (event) => {
    clearStreamTimeout()
    onDone?.(parseMessageEvent(event))
    close()
  })

  eventSource.addEventListener('server_error', (event) => {
    clearStreamTimeout()
    onServerError?.(parseMessageEvent(event))
    close()
  })

  eventSource.addEventListener('heartbeat', (event) => {
    resetStreamTimeout()
    const data = parseMessageEvent(event)
    console.log('SSE heartbeat:', data.message)
  })

  eventSource.addEventListener('error', () => {
    if (!closed) {
      clearStreamTimeout()
      onConnectionError?.()
      close()
    }
  })

  return {
    close,
  }
}