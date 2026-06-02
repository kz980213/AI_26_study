export type ToolName = 'create_task' | 'list_recent_tasks'

export interface ToolCallExecuteResponse {
  success: boolean
  tool_name: ToolName
  arguments: Record<string, unknown>
  tool_result: Record<string, unknown>
  raw_text: string
  elapsed_ms: number
  retry_count: number
  log_id?: number | null
}

export interface ToolCallLogRecord {
  id: number
  source_text: string
  tool_name?: string | null
  arguments_json?: string | null
  tool_result_json?: string | null
  raw_text?: string | null
  status: string
  error_message?: string | null
  elapsed_ms: number
  retry_count: number
  created_at: string
}

export interface ToolCallLogListResponse {
  items: ToolCallLogRecord[]
}

export interface ToolDefinitionItem {
  name: string
  description: string
  arguments_schema: Record<string, unknown>
}

export interface ToolDefinitionListResponse {
  items: ToolDefinitionItem[]
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

export async function fetchRecentToolCallLogs(
  limit = 20
): Promise<ToolCallLogRecord[]> {
  const response = await fetch(
    `${API_BASE_URL}/ai/tools/logs/recent?limit=${limit}`
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取工具调用日志失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.items || []
}

export async function fetchAvailableTools(): Promise<ToolDefinitionItem[]> {
  const response = await fetch(`${API_BASE_URL}/ai/tools/available`)

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取可用工具列表失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.items || []
}