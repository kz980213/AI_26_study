const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export interface ChatHistoryMessage {
  id: string
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  request_id?: string
  created_at?: string
}

export async function fetchConversationMessages(
  conversationId: string,
): Promise<ChatHistoryMessage[]> {
  const response = await fetch(
    `${API_BASE_URL}/ai/chat/conversations/${conversationId}/messages`,
  )

  if (!response.ok) {
    throw new Error(`加载历史消息失败：${response.status}`)
  }

  return response.json()
}

export interface ChatConversation {
  id: string
  title: string
  created_at?: string
  updated_at?: string
}

export interface SaveChatMessagePayload {
  conversation_id: string
  role: 'user' | 'assistant'
  content: string
  request_id?: string
}

export async function fetchConversations(limit = 20): Promise<ChatConversation[]> {
  const response = await fetch(
    `${API_BASE_URL}/ai/chat/conversations?limit=${limit}`,
  )

  if (!response.ok) {
    throw new Error(`加载会话列表失败：${response.status}`)
  }

  return response.json()
}

export async function saveChatMessage(payload: SaveChatMessagePayload) {
  const response = await fetch(`${API_BASE_URL}/ai/chat/messages`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    throw new Error(`保存聊天消息失败：${response.status}`)
  }

  return response.json()
}