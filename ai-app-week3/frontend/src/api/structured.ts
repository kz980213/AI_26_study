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
  retry_count: number
  id?: number | null
  created_at?: string | null
}

export interface StructuredTaskRecord {
  id: number
  source_text: string
  title: string
  category: string
  priority: 'low' | 'medium' | 'high'
  due_time?: string | null
  description?: string | null
  raw_text?: string | null
  retry_count: number
  elapsed_ms: number
  created_at: string
}

export interface StructuredTaskRecordListResponse {
  items: StructuredTaskRecord[]
}

export interface StructuredTaskDetailResponse {
  item: StructuredTaskRecord
}

export interface StructuredTaskUpdatePayload {
  title: string
  category: string
  priority: 'low' | 'medium' | 'high'
  due_time?: string | null
  description?: string | null
}

export interface StructuredTaskUpdateResponse {
  success: boolean
  item: StructuredTaskRecord
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

export async function fetchRecentStructuredTasks(
  limit = 20
): Promise<StructuredTaskRecord[]> {
  const response = await fetch(
    `${API_BASE_URL}/ai/structured/tasks/recent?limit=${limit}`
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取最近结构化任务失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.items || []
}

export async function fetchStructuredTaskDetail(
  taskId: number
): Promise<StructuredTaskRecord> {
  const response = await fetch(
    `${API_BASE_URL}/ai/structured/tasks/${taskId}`
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '获取结构化任务详情失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.item
}


export async function updateStructuredTask(
  taskId: number,
  payload: StructuredTaskUpdatePayload
): Promise<StructuredTaskRecord> {
  const response = await fetch(
    `${API_BASE_URL}/ai/structured/tasks/${taskId}`,
    {
      method: 'PATCH',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(payload),
    }
  )

  const result = await response.json().catch(() => null)

  if (!response.ok) {
    const message =
      result?.detail?.message ||
      result?.detail ||
      '保存结构化任务失败'

    throw new Error(
      typeof message === 'string' ? message : JSON.stringify(message)
    )
  }

  return result.item
}