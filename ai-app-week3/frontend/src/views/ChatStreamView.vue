<template>
  <div class="chat-layout">
    <aside class="conversation-panel">
      <div class="conversation-header">
        <div class="conversation-title">最近会话</div>

        <button class="small-btn" :disabled="isStreaming" @click="startNewConversation">新会话</button>
      </div>

      <div v-if="loadingConversations" class="conversation-empty">加载中...</div>

      <div v-else-if="conversations.length === 0" class="conversation-empty">暂无会话</div>

      <div v-else class="conversation-list">
        <button
          v-for="item in conversations"
          :key="item.id"
          class="conversation-item"
          :class="{ active: item.id === conversationId }"
          :disabled="isStreaming"
          @click="switchConversation(item.id)"
        >
          <div class="conversation-name">{{ item.title || '新会话' }}</div>

          <div class="conversation-time">{{ item.updated_at || item.created_at || '' }}</div>
        </button>
      </div>
    </aside>
    <div class="chat-page">
      <div class="header">
        <h2>Week4 Day04：真实 DeepSeek SSE 流式聊天</h2>
        <p>目标：前端通过 EventSource 连接 FastAPI，后端转发 DeepSeek 的真实流式输出。</p>
      </div>

      <div class="summary-card">
        <div class="summary-header">
          <div>
            <div class="summary-title">最近 20 次模型调用统计</div>
            <div class="summary-subtitle">用于观察 token、耗时、成功率和估算成本</div>
          </div>

          <button
            class="small-btn"
            :disabled="loadingUsageSummary"
            @click="loadUsageSummary"
          >{{ loadingUsageSummary ? '刷新中...' : '刷新统计' }}</button>
        </div>

        <div v-if="!usageSummary" class="summary-empty">暂无统计数据，先发送一次真实模型请求。</div>

        <div v-else class="summary-grid">
          <div class="summary-item">
            <span class="summary-label">调用次数</span>
            <strong>{{ usageSummary.total_calls }}</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">成功率</span>
            <strong>{{ usageSummary.success_rate }}%</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">失败次数</span>
            <strong>{{ usageSummary.error_calls }}</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">平均耗时</span>
            <strong>{{ usageSummary.avg_elapsed_ms }} ms</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">输入 Token</span>
            <strong>{{ usageSummary.total_prompt_tokens_est }}</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">输出 Token</span>
            <strong>{{ usageSummary.total_completion_tokens_est }}</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">总 Token</span>
            <strong>{{ usageSummary.total_tokens_est }}</strong>
          </div>

          <div class="summary-item">
            <span class="summary-label">估算成本</span>
            <strong>¥{{ usageSummary.estimated_total_cost_cny }}</strong>
          </div>
        </div>

        <div v-if="usageSummary" class="summary-tip">当前成本基于 .env 中配置的单价估算，不代表模型厂商最终账单。</div>
      </div>

      <div class="chat-card" ref="chatCardRef">
        <div v-if="messages.length === 0" class="empty">还没有消息。输入一句话，开始测试封装后的 SSE 聊天流。</div>

        <div
          v-for="message in messages"
          :key="message.id"
          class="message-row"
          :class="message.role"
        >
          <div class="avatar">{{ message.role === 'user' ? '我' : 'AI' }}</div>

          <div class="bubble">
            <div class="role-name">
              {{ message.role === 'user' ? '用户' : '助手' }}
              <span
                v-if="message.status === 'streaming'"
                class="streaming-tag"
              >输出中</span>

              <span v-if="message.status === 'error'" class="error-tag">异常</span>
            </div>

            <div class="content">
              {{ message.content }}
              <span
                v-if="message.role === 'assistant' && message.status === 'streaming'"
                class="cursor"
              >|</span>
            </div>
          </div>
        </div>
      </div>

      <div class="input-card">
        <textarea
          v-model="inputText"
          class="textarea"
          placeholder="例如：请解释什么是 SSE"
          :disabled="isStreaming"
          @keydown.enter.exact.prevent="() => sendMessage()"
        />

        <div class="button-row">
          <button
            class="btn primary"
            :disabled="!inputText.trim() || isStreaming"
            @click="sendMessage"
          >发送</button>

          <button class="btn" :disabled="!isStreaming" @click="stopStream">停止输出</button>

          <button class="btn" :disabled="isStreaming" @click="startNewConversation">新会话</button>

          <button
            class="btn"
            :disabled="!conversationId || isStreaming"
            @click="loadConversationMessages()"
          >重新加载历史</button>
        </div>

        <div class="tips">当前状态：{{ statusText }}</div>
        <div v-if="currentRequestId" class="request-id">request_id：{{ currentRequestId }}</div>
        <div v-if="llmUsageInfo.model || llmUsageInfo.total_tokens_est" class="usage-box">
          <div class="usage-title">本次模型调用</div>

          <div class="usage-grid">
            <div>Provider：{{ llmUsageInfo.provider || '-' }}</div>
            <div>Model：{{ llmUsageInfo.model || '-' }}</div>
            <div>输入估算 Token：{{ llmUsageInfo.prompt_tokens_est ?? '-' }}</div>
            <div>输出估算 Token：{{ llmUsageInfo.completion_tokens_est ?? '-' }}</div>
            <div>总估算 Token：{{ llmUsageInfo.total_tokens_est ?? '-' }}</div>
            <div>耗时：{{ llmUsageInfo.elapsed_ms ?? '-' }} ms</div>
          </div>

          <div class="usage-tip">当前 token 为粗略估算值，后续会替换为模型厂商返回的精确 usage。</div>
        </div>

        <div v-if="errorText" class="error-box">
          <div class="error-title">本次请求失败</div>
          <pre>{{ errorText }}</pre>

          <button
            class="btn retry"
            :disabled="isStreaming || !lastUserMessage"
            @click="retryLastMessage"
          >重试上一次问题</button>
        </div>
      </div>

      <div class="log-card">
        <div class="log-title">事件日志</div>

        <div v-if="logs.length === 0" class="log-empty">暂无日志</div>

        <ul v-else class="logs">
          <li v-for="(log, index) in logs" :key="index">{{ log }}</li>
        </ul>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, onMounted, ref } from 'vue'
import {
  createChatStream,
  type ChatStreamController,
  type ChatStreamPayload,
} from '@/utils/sseClient'
import { 
  fetchConversations,
  fetchConversationMessages,
  saveChatMessage,
  type ChatConversation, 
} from '../api/chatSse'
import {
  fetchLLMUsageSummary,
  type LLMUsageSummary,
} from '../api/llmUsage'

type MessageRole = 'user' | 'assistant'
type MessageStatus = 'done' | 'streaming' | 'error'

interface ChatMessage {
  id: string
  role: MessageRole
  content: string
  status?: MessageStatus
}

const inputText = ref('')
const messages = ref<ChatMessage[]>([])
const logs = ref<string[]>([])
const isStreaming = ref(false)
const conversationId = ref<string>('')
const chatCardRef = ref<HTMLElement | null>(null)
const lastUserMessage = ref('')
const errorText = ref('')
const currentRequestId = ref('')

const CHAT_CONVERSATION_ID_KEY = 'week4_chat_conversation_id'

const conversations = ref<ChatConversation[]>([])
const loadingConversations = ref(false)

const llmUsageInfo = ref<{
  provider?: string
  model?: string
  prompt_tokens_est?: number
  completion_tokens_est?: number
  total_tokens_est?: number
  elapsed_ms?: number
}>({})

const usageSummary = ref<LLMUsageSummary | null>(null)
const loadingUsageSummary = ref(false)

let streamController: ChatStreamController | null = null
let currentAssistantMessageId = ''

const statusText = computed(() => {
  if (isStreaming.value) {
    return 'AI 正在流式输出'
  }

  if (conversationId.value) {
    return `空闲，会话ID：${conversationId.value}`
  }

  return '空闲'
})

function createMessageId() {
  return `${Date.now()}-${Math.random().toString(16).slice(2)}`
}

function addLog(message: string) {
  const time = new Date().toLocaleTimeString()
  logs.value.unshift(`[${time}] ${message}`)
}

function findAssistantMessage() {
  return messages.value.find((item) => item.id === currentAssistantMessageId)
}

function closeStream() {
  if (streamController) {
    streamController.close()
    streamController = null
  }
}

async function scrollToBottom() {
  await nextTick()

  if (chatCardRef.value) {
    chatCardRef.value.scrollTop = chatCardRef.value.scrollHeight
  }
}

function appendAssistantContent(content = '') {
  const assistant = findAssistantMessage()

  if (!assistant) {
    return
  }

  assistant.content += content
  assistant.status = 'streaming'

  scrollToBottom()
}

function finishAssistantMessage() {
  const assistant = findAssistantMessage()

  if (assistant) {
    assistant.status = 'done'
  }

  isStreaming.value = false
  closeStream()
}

function markAssistantError(message: string) {
  const assistant = findAssistantMessage()

  if (assistant) {
    assistant.status = 'error'

    if (!assistant.content) {
      assistant.content = message
    } else {
      assistant.content += `\n\n${message}`
    }
  }

  isStreaming.value = false
  closeStream()
  scrollToBottom()
}

function sendMessage(messageOverride?: string) {
  const text = (messageOverride ?? inputText.value).trim()

  if (!text || isStreaming.value) {
    return
  }

  closeStream()

  lastUserMessage.value = text
  errorText.value = ''
  currentRequestId.value = ''

  const userMessage: ChatMessage = {
    id: createMessageId(),
    role: 'user',
    content: text,
    status: 'done',
  }

  const assistantMessage: ChatMessage = {
    id: createMessageId(),
    role: 'assistant',
    content: '',
    status: 'streaming',
  }

  messages.value.push(userMessage, assistantMessage)

  currentAssistantMessageId = assistantMessage.id
  inputText.value = ''
  isStreaming.value = true

  scrollToBottom()

  addLog('开始创建 DeepSeek SSE 连接')

  streamController = createChatStream({
    message: text,
    conversationId: conversationId.value || undefined,
    endpoint: '/ai/chat/stream/deepseek',
    timeoutMs: 60000,

    onOpen: () => {
      addLog('SSE 连接已打开')
    },

    onStart: (data: ChatStreamPayload) => {
        if (data.conversation_id) {
          conversationId.value = data.conversation_id
          localStorage.setItem(CHAT_CONVERSATION_ID_KEY, data.conversation_id)
        }
      
        if (data.request_id) {
          currentRequestId.value = data.request_id
        }
        llmUsageInfo.value = {
          provider: data.provider,
          model: data.model,
          prompt_tokens_est: data.prompt_tokens_est,
        }
        addLog(
          `后端开始输出，conversation_id=${data.conversation_id || '-'}，request_id=${data.request_id || '-'}`,
        )
    },
    
    onChunk: (data: ChatStreamPayload) => {
      appendAssistantContent(data.content || '')
      addLog(`收到 chunk ${data.index}: ${data.content || ''}`)
    },

    onDone: (data: ChatStreamPayload) => {
      llmUsageInfo.value = {
        provider: data.provider,
        model: data.model,
        prompt_tokens_est: data.prompt_tokens_est,
        completion_tokens_est: data.completion_tokens_est,
        total_tokens_est: data.total_tokens_est,
        elapsed_ms: data.elapsed_ms,
      }
    
      finishAssistantMessage()
    
      addLog(
        `流式输出完成，耗时：${data.elapsed_ms || '-'} ms，估算 total_tokens=${data.total_tokens_est || '-'}`,
      )
    
      void loadConversations()
      void loadUsageSummary()
    },

    onServerError: (data: ChatStreamPayload) => {
      const message = [
        `服务端错误：${data.error_code || 'UNKNOWN_ERROR'}`,
        data.status_code ? `HTTP 状态码：${data.status_code}` : '',
        data.request_id ? `request_id：${data.request_id}` : '',
        data.message ? `错误信息：${data.message}` : '',
      ]
        .filter(Boolean)
        .join('\n')

      errorText.value = message
      currentRequestId.value = data.request_id || ''

      markAssistantError(message)
      llmUsageInfo.value = {
        provider: data.provider,
        model: data.model,
        prompt_tokens_est: data.prompt_tokens_est,
        completion_tokens_est: data.completion_tokens_est,
        total_tokens_est: data.total_tokens_est,
        elapsed_ms: data.elapsed_ms,
      }
      addLog(`服务端异常：${data.error_code || '-'} request_id=${data.request_id || '-'}`)
      void loadUsageSummary()
    },

    onConnectionError: () => {
      const message = 'SSE 连接异常或超时，请检查后端服务、网络或 CORS。'

      errorText.value = message
      markAssistantError(message)
      addLog('SSE 连接异常或超时')
    },
  })
}

function retryLastMessage() {
  if (!lastUserMessage.value || isStreaming.value) {
    return
  }

  addLog(`重试上一次问题：${lastUserMessage.value}`)
  sendMessage(lastUserMessage.value)
}

async function stopStream() {
  const assistant = findAssistantMessage()
  let contentToSave = ''

  if (assistant && assistant.status === 'streaming') {
    assistant.status = 'done'
    assistant.content += '\n\n[你已手动停止输出]'
    contentToSave = assistant.content
  }

  isStreaming.value = false
  addLog('已手动停止输出')

  closeStream()

  if (conversationId.value && contentToSave.trim()) {
    try {
      await saveChatMessage({
        conversation_id: conversationId.value,
        role: 'assistant',
        content: contentToSave,
        request_id: currentRequestId.value || undefined,
      })

      addLog('已保存停止时的部分 assistant 回复')
      await loadConversations()
    } catch (error) {
      addLog(`保存停止时的部分回复失败：${String(error)}`)
    }
  }
}

function clearMessages() {
  messages.value = []
  logs.value = []
  inputText.value = ''
  isStreaming.value = false
  conversationId.value = ''
  currentAssistantMessageId = ''
  currentRequestId.value = ''
  errorText.value = ''
  llmUsageInfo.value = {}
  localStorage.removeItem(CHAT_CONVERSATION_ID_KEY)

  closeStream()
}

async function loadConversationMessages(conversationIdOverride?: string) {
  const targetConversationId = conversationIdOverride || conversationId.value

  if (!targetConversationId) {
    return
  }

  try {
    addLog(`开始加载历史消息：${targetConversationId}`)

    const historyMessages = await fetchConversationMessages(targetConversationId)

    messages.value = historyMessages.map((item) => ({
      id: item.id,
      role: item.role,
      content: item.content,
      status: 'done',
    }))

    conversationId.value = targetConversationId
    localStorage.setItem(CHAT_CONVERSATION_ID_KEY, targetConversationId)

    addLog(`历史消息加载完成，共 ${historyMessages.length} 条`)
    scrollToBottom()
  } catch (error) {
    addLog(`加载历史消息失败：${String(error)}`)
  }
}

async function loadConversations() {
  try {
    loadingConversations.value = true
    conversations.value = await fetchConversations(20)
  } catch (error) {
    addLog(`加载会话列表失败：${String(error)}`)
  } finally {
    loadingConversations.value = false
  }
}

async function switchConversation(targetConversationId: string) {
  if (isStreaming.value) {
    addLog('当前正在输出中，不能切换会话')
    return
  }

  conversationId.value = targetConversationId
  localStorage.setItem(CHAT_CONVERSATION_ID_KEY, targetConversationId)

  await loadConversationMessages(targetConversationId)
}

function startNewConversation() {
  llmUsageInfo.value = {}
  if (isStreaming.value) {
    return
  }

  messages.value = []
  logs.value = []
  inputText.value = ''
  conversationId.value = ''
  currentAssistantMessageId = ''
  currentRequestId.value = ''
  errorText.value = ''

  localStorage.removeItem(CHAT_CONVERSATION_ID_KEY)

  addLog('已创建新会话，本地状态已清空')
}

async function loadUsageSummary() {
  try {
    loadingUsageSummary.value = true
    usageSummary.value = await fetchLLMUsageSummary(20)
    addLog('LLM 使用统计已刷新')
  } catch (error) {
    addLog(`加载 LLM 使用统计失败：${String(error)}`)
  } finally {
    loadingUsageSummary.value = false
  }
}

onMounted(async () => {
  await loadConversations()
  await loadUsageSummary()

  const savedConversationId = localStorage.getItem(CHAT_CONVERSATION_ID_KEY)

  if (savedConversationId) {
    conversationId.value = savedConversationId
    await loadConversationMessages(savedConversationId)
  }
})

onBeforeUnmount(() => {
  closeStream()
})
</script>

<style scoped>
.chat-layout {
  display: flex;
  min-height: 100vh;
  background: #f3f4f6;
}

.conversation-panel {
  width: 260px;
  flex-shrink: 0;
  padding: 16px;
  border-right: 1px solid #e5e7eb;
  background: #ffffff;
}

.conversation-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;
}

.conversation-title {
  font-weight: 700;
  font-size: 16px;
}

.small-btn {
  padding: 6px 10px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  cursor: pointer;
  font-size: 12px;
}

.small-btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.conversation-empty {
  padding: 24px 0;
  text-align: center;
  color: #9ca3af;
  font-size: 13px;
}

.conversation-list {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.conversation-item {
  width: 100%;
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #ffffff;
  text-align: left;
  cursor: pointer;
}

.conversation-item.active {
  border-color: #2563eb;
  background: #eff6ff;
}

.conversation-item:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.conversation-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  color: #111827;
  font-size: 14px;
  font-weight: 600;
}

.conversation-time {
  margin-top: 4px;
  color: #9ca3af;
  font-size: 11px;
}

.chat-page {
  flex: 1;
  max-width: none;
  margin: 0;
  padding: 24px;
  font-family: Arial, "Microsoft YaHei", sans-serif;
}

@media (max-width: 768px) {
  .chat-layout {
    flex-direction: column;
  }

  .conversation-panel {
    width: auto;
    border-right: none;
    border-bottom: 1px solid #e5e7eb;
  }
}

.header {
  margin-bottom: 16px;
}

.header h2 {
  margin: 0 0 8px;
}

.header p {
  margin: 0;
  color: #6b7280;
}

.chat-card {
  height: 420px;
  overflow-y: auto;
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #f9fafb;
}

.empty {
  padding: 120px 0;
  text-align: center;
  color: #9ca3af;
}

.message-row {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}

.message-row.user {
  flex-direction: row-reverse;
}

.avatar {
  width: 36px;
  height: 36px;
  flex-shrink: 0;
  line-height: 36px;
  text-align: center;
  border-radius: 50%;
  background: #e5e7eb;
  font-size: 13px;
  font-weight: 600;
}

.message-row.user .avatar {
  color: #ffffff;
  background: #2563eb;
}

.message-row.assistant .avatar {
  color: #ffffff;
  background: #111827;
}

.bubble {
  max-width: 72%;
  padding: 12px 14px;
  border-radius: 12px;
  background: #ffffff;
  border: 1px solid #e5e7eb;
}

.message-row.user .bubble {
  color: #ffffff;
  background: #2563eb;
  border-color: #2563eb;
}

.role-name {
  margin-bottom: 6px;
  font-size: 12px;
  opacity: 0.8;
}

.content {
  white-space: pre-wrap;
  line-height: 1.7;
  font-size: 15px;
}

.streaming-tag {
  margin-left: 8px;
  color: #2563eb;
}

.error-tag {
  margin-left: 8px;
  color: #dc2626;
}

.cursor {
  margin-left: 2px;
  animation: blink 1s infinite;
}

.input-card,
.log-card {
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
}

.textarea {
  width: 100%;
  min-height: 88px;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  resize: vertical;
  font-size: 14px;
  outline: none;
}

.textarea:focus {
  border-color: #2563eb;
}

.button-row {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.btn {
  padding: 8px 16px;
  border: 1px solid #d1d5db;
  border-radius: 9px;
  background: #f9fafb;
  cursor: pointer;
}

.btn.primary {
  color: #ffffff;
  border-color: #2563eb;
  background: #2563eb;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.55;
}

.tips {
  margin-top: 10px;
  color: #6b7280;
  font-size: 13px;
}

.log-title {
  margin-bottom: 8px;
  font-weight: 600;
}

.log-empty {
  color: #9ca3af;
}

.logs {
  max-height: 180px;
  overflow: auto;
  padding-left: 20px;
  color: #4b5563;
  line-height: 1.7;
  font-size: 13px;
}

@keyframes blink {
  0% {
    opacity: 1;
  }

  50% {
    opacity: 0;
  }

  100% {
    opacity: 1;
  }
}
.request-id {
  margin-top: 8px;
  color: #6b7280;
  font-size: 12px;
}

.error-box {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #fecaca;
  border-radius: 10px;
  background: #fef2f2;
  color: #991b1b;
}

.error-title {
  margin-bottom: 6px;
  font-weight: 600;
}

.error-box pre {
  margin: 0 0 10px;
  white-space: pre-wrap;
  font-family: inherit;
  font-size: 13px;
  line-height: 1.6;
}

.btn.retry {
  color: #ffffff;
  border-color: #dc2626;
  background: #dc2626;
}
.usage-box {
  margin-top: 12px;
  padding: 12px;
  border: 1px solid #bfdbfe;
  border-radius: 10px;
  background: #eff6ff;
  color: #1e3a8a;
}

.usage-title {
  margin-bottom: 8px;
  font-weight: 700;
}

.usage-grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 6px 12px;
  font-size: 13px;
  line-height: 1.6;
}

.usage-tip {
  margin-top: 8px;
  color: #64748b;
  font-size: 12px;
}
.summary-card {
  padding: 16px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 14px;
  background: #ffffff;
}

.summary-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
}

.summary-title {
  font-weight: 700;
  color: #111827;
}

.summary-subtitle {
  margin-top: 4px;
  color: #6b7280;
  font-size: 12px;
}

.summary-empty {
  padding: 16px 0;
  color: #9ca3af;
  font-size: 13px;
}

.summary-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 10px;
}

.summary-item {
  padding: 10px;
  border: 1px solid #e5e7eb;
  border-radius: 10px;
  background: #f9fafb;
}

.summary-label {
  display: block;
  margin-bottom: 4px;
  color: #6b7280;
  font-size: 12px;
}

.summary-item strong {
  color: #111827;
  font-size: 16px;
}

.summary-tip {
  margin-top: 10px;
  color: #64748b;
  font-size: 12px;
}

@media (max-width: 900px) {
  .summary-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
</style>