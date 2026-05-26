<template>
  <div class="chat-page">
    <div class="header">
      <h2>Week4 Day04：真实 DeepSeek SSE 流式聊天</h2>
      <p>目标：前端通过 EventSource 连接 FastAPI，后端转发 DeepSeek 的真实流式输出。</p>
    </div>

    <div class="chat-card" ref="chatCardRef">
      <div v-if="messages.length === 0" class="empty">
        还没有消息。输入一句话，开始测试封装后的 SSE 聊天流。
      </div>

      <div
        v-for="message in messages"
        :key="message.id"
        class="message-row"
        :class="message.role"
      >
        <div class="avatar">
          {{ message.role === 'user' ? '我' : 'AI' }}
        </div>

        <div class="bubble">
          <div class="role-name">
            {{ message.role === 'user' ? '用户' : '助手' }}

            <span v-if="message.status === 'streaming'" class="streaming-tag">
              输出中
            </span>

            <span v-if="message.status === 'error'" class="error-tag">
              异常
            </span>
          </div>

          <div class="content">
            {{ message.content }}
            <span
              v-if="message.role === 'assistant' && message.status === 'streaming'"
              class="cursor"
            >
              |
            </span>
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
        @keydown.enter.exact.prevent="sendMessage"
      />

      <div class="button-row">
        <button
          class="btn primary"
          :disabled="!inputText.trim() || isStreaming"
          @click="sendMessage"
        >
          发送
        </button>

        <button
          class="btn"
          :disabled="!isStreaming"
          @click="stopStream"
        >
          停止输出
        </button>

        <button
          class="btn"
          :disabled="isStreaming"
          @click="clearMessages"
        >
          清空
        </button>
      </div>

      <div class="tips">
        当前状态：{{ statusText }}
      </div>
    </div>

    <div class="log-card">
      <div class="log-title">事件日志</div>

      <div v-if="logs.length === 0" class="log-empty">
        暂无日志
      </div>

      <ul v-else class="logs">
        <li v-for="(log, index) in logs" :key="index">
          {{ log }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, nextTick, onBeforeUnmount, ref } from 'vue'
import {
  createChatStream,
  type ChatStreamController,
  type ChatStreamPayload,
} from '@/utils/sseClient'

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

function sendMessage() {
  const text = inputText.value.trim()

  if (!text || isStreaming.value) {
    return
  }

  closeStream()

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

  addLog('开始创建 SSE 连接')

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
      }

      addLog(`后端开始输出，会话ID：${data.conversation_id || '-'}`)
    },

    onChunk: (data: ChatStreamPayload) => {
      appendAssistantContent(data.content || '')
      addLog(`收到 chunk ${data.index}: ${data.content || ''}`)
    },

    onDone: () => {
      finishAssistantMessage()
      addLog('流式输出完成')
    },

    onServerError: (data: ChatStreamPayload) => {
      markAssistantError(data.message || '服务端返回异常')
      addLog(`服务端异常：${data.message || '-'}`)
    },

    onConnectionError: () => {
      markAssistantError('SSE 连接异常或超时，请检查后端服务。')
      addLog('SSE 连接异常或超时')
    },
  })
}

function stopStream() {
  const assistant = findAssistantMessage()

  if (assistant && assistant.status === 'streaming') {
    assistant.status = 'done'
    assistant.content += '\n\n[你已手动停止输出]'
  }

  isStreaming.value = false
  addLog('已手动停止输出')

  closeStream()
}

function clearMessages() {
  messages.value = []
  logs.value = []
  inputText.value = ''
  isStreaming.value = false
  conversationId.value = ''
  currentAssistantMessageId = ''

  closeStream()
}

onBeforeUnmount(() => {
  closeStream()
})
</script>

<style scoped>
.chat-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 24px;
  font-family: Arial, "Microsoft YaHei", sans-serif;
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
</style>