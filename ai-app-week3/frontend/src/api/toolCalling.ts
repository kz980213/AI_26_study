export type ToolName = 'create_task' | 'list_recent_tasks'

export interface ToolCallExecuteResponse {
  success: boolean
  tool_name: ToolName
  arguments: Record<string, unknown>
  tool_result: Record<string, unknown>
  raw_text: string
  elapsed_ms: number
}

const API_BASE_URL =
  import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export async function executeAiTool(
  text: string
): Promise<ToolCallExecuteResponse> {
  const response = await fetch(`${API_BASE_URL}/ai/tools/execute`, {
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
      'AI 工具调用失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result
}