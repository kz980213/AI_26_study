const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export interface ChatPromptVersionItem {
  version: string
  name: string
  description: string
}

export interface ChatPromptInfo {
  template_name: string
  version: string
  template: string
  variables: Record<string, string>
  preview: string
  available_versions: ChatPromptVersionItem[]
  default_version: string
}

export async function fetchChatPromptInfo(
  promptVersion?: string,
): Promise<ChatPromptInfo> {
  const params = new URLSearchParams()

  if (promptVersion) {
    params.set('prompt_version', promptVersion)
  }

  const query = params.toString()
  const url = `${API_BASE_URL}/ai/prompts/chat${query ? `?${query}` : ''}`

  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`加载 Prompt 信息失败：${response.status}`)
  }

  return response.json()
}