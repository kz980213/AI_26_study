const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8010'

export interface LLMCallLogItem {
  id: string
  request_id: string
  conversation_id?: string
  provider: string
  model: string
  status: 'success' | 'error'
  error_code?: string
  status_code?: number
  prompt_tokens_est: number
  completion_tokens_est: number
  total_tokens_est: number
  elapsed_ms?: number
  estimated_cost_cny: number
  created_at?: string
}

export interface LLMUsageSummary {
  limit: number
  total_calls: number
  success_calls: number
  error_calls: number
  success_rate: number
  total_prompt_tokens_est: number
  total_completion_tokens_est: number
  total_tokens_est: number
  avg_elapsed_ms: number
  estimated_input_cost_cny: number
  estimated_output_cost_cny: number
  estimated_total_cost_cny: number
  recent_logs: LLMCallLogItem[]
  prompt_template_name?: string
  prompt_version?: string
  system_prompt_preview?: string
}

export async function fetchLLMUsageSummary(limit = 20): Promise<LLMUsageSummary> {
  const response = await fetch(`${API_BASE_URL}/ai/llm/usage-summary?limit=${limit}`)

  if (!response.ok) {
    throw new Error(`加载 LLM 使用统计失败：${response.status}`)
  }

  return response.json()
}