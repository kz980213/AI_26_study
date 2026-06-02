export interface StructuredTask {
  title: string
  category: string
  priority: 'low' | 'medium' | 'high'
  due_time?: string | null
  description?: string | null
}

export interface StructuredTaskExtractResponse {
  success: boolean
  data: StructuredTask
  raw_text: string
  elapsed_ms: number
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export async function extractTaskFromText(
  text: string
): Promise<StructuredTaskExtractResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/structured/tasks/extract`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ text }),
  })

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '结构化任务抽取失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result
}