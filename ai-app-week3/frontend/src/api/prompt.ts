const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export interface ChatPromptInfo {
  template_name: string
  version: string
  template: string
  variables: Record<string, string>
  preview: string
}

export async function fetchChatPromptInfo(): Promise<ChatPromptInfo> {
  const response = await fetch(`${API_BASE_URL}/ai/prompts/chat`)

  if (!response.ok) {
    throw new Error(`加载 Prompt 信息失败：${response.status}`)
  }

  return response.json()
}