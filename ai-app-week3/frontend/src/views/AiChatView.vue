<template>
  <div class="stream-page">
    <h2>第4周 Day01：SSE 流式输出 Demo</h2>

    <div class="form-card">
      <label class="label">输入一句提示词：</label>

      <textarea
        v-model="prompt"
        class="textarea"
        placeholder="例如：请用一句话解释什么是 SSE"
      />

      <div class="button-row">
        <button
          class="btn primary"
          :disabled="status === 'streaming' || status === 'connecting'"
          @click="startStream"
        >
          开始流式输出
        </button>

        <button
          class="btn"
          :disabled="!eventSource"
          @click="stopStream"
        >
          停止
        </button>

        <button class="btn" @click="clearContent">
          清空
        </button>
      </div>

      <p class="status">
        当前状态：
        <span :class="statusClass">{{ statusText }}</span>
      </p>
    </div>

    <div class="result-card">
      <div class="result-title">模型输出区域：</div>

      <div v-if="!content" class="placeholder">
        点击“开始流式输出”后，这里会一段一段显示后端推送的内容。
      </div>

      <div v-else class="content">
        {{ content }}
        <span v-if="status === 'streaming'" class="cursor">|</span>
      </div>
    </div>

    <div class="log-card">
      <div class="result-title">事件日志：</div>

      <div v-if="logs.length === 0" class="placeholder">
        暂无日志
      </div>

      <ul v-else class="logs">
        <li v-for="(item, index) in logs" :key="index">
          {{ item }}
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onBeforeUnmount, ref } from 'vue'

const API_BASE_URL = 'http://127.0.0.1:8010'

const prompt = ref('请演示一个 SSE 流式输出效果')
const content = ref('')
const logs = ref<string[]>([])
const status = ref<'idle' | 'connecting' | 'streaming' | 'done' | 'error'>('idle')

let eventSource: EventSource | null = null

const statusText = computed(() => {
  const map = {
    idle: '空闲',
    connecting: '连接中',
    streaming: '输出中',
    done: '已完成',
    error: '异常',
  }

  return map[status.value]
})

const statusClass = computed(() => {
  return {
    'status-idle': status.value === 'idle',
    'status-connecting': status.value === 'connecting',
    'status-streaming': status.value === 'streaming',
    'status-done': status.value === 'done',
    'status-error': status.value === 'error',
  }
})

function addLog(message: string) {
  const time = new Date().toLocaleTimeString()
  logs.value.unshift(`[${time}] ${message}`)
}

function closeEventSource() {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }
}

function startStream() {
  closeEventSource()

  content.value = ''
  logs.value = []
  status.value = 'connecting'

  const url = `${API_BASE_URL}/ai/stream?prompt=${encodeURIComponent(prompt.value)}`

  addLog(`准备连接：${url}`)

  eventSource = new EventSource(url)

  eventSource.addEventListener('open', () => {
    status.value = 'streaming'
    addLog('SSE 连接已打开')
  })

  eventSource.addEventListener('start', (event) => {
    const data = JSON.parse((event as MessageEvent).data)
    addLog(`后端开始推送，prompt：${data.prompt}`)
  })

  eventSource.addEventListener('message', (event) => {
    const data = JSON.parse((event as MessageEvent).data)

    if (data.type === 'chunk') {
      content.value += data.content
      addLog(`收到第 ${data.index + 1} 段：${data.content}`)
    }
  })

  eventSource.addEventListener('done', (event) => {
    const data = JSON.parse((event as MessageEvent).data)

    status.value = 'done'
    addLog(data.message || '流式输出完成')

    closeEventSource()
  })

  eventSource.addEventListener('error', () => {
    if (status.value !== 'done') {
      status.value = 'error'
      addLog('SSE 连接异常，请检查后端服务、CORS 或接口地址')
    }

    closeEventSource()
  })
}

function stopStream() {
  closeEventSource()
  status.value = 'idle'
  addLog('已手动停止 SSE 连接')
}

function clearContent() {
  content.value = ''
  logs.value = []
  status.value = 'idle'
  closeEventSource()
}

onBeforeUnmount(() => {
  closeEventSource()
})
</script>

<style scoped>
.stream-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
  font-family: Arial, "Microsoft YaHei", sans-serif;
}

h2 {
  margin-bottom: 20px;
}

.form-card,
.result-card,
.log-card {
  padding: 20px;
  margin-bottom: 16px;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  background: #ffffff;
}

.label {
  display: block;
  margin-bottom: 8px;
  font-weight: 600;
}

.textarea {
  width: 100%;
  min-height: 90px;
  box-sizing: border-box;
  padding: 12px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  resize: vertical;
  font-size: 14px;
}

.button-row {
  display: flex;
  gap: 12px;
  margin-top: 12px;
}

.btn {
  padding: 8px 14px;
  border: 1px solid #d1d5db;
  border-radius: 8px;
  background: #f9fafb;
  cursor: pointer;
}

.btn:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.btn.primary {
  color: #ffffff;
  border-color: #2563eb;
  background: #2563eb;
}

.status {
  margin-top: 12px;
}

.status-idle {
  color: #6b7280;
}

.status-connecting {
  color: #d97706;
}

.status-streaming {
  color: #2563eb;
}

.status-done {
  color: #16a34a;
}

.status-error {
  color: #dc2626;
}

.result-title {
  margin-bottom: 10px;
  font-weight: 600;
}

.placeholder {
  color: #9ca3af;
}

.content {
  min-height: 100px;
  line-height: 1.8;
  white-space: pre-wrap;
  font-size: 16px;
}

.cursor {
  display: inline-block;
  margin-left: 2px;
  animation: blink 1s infinite;
}

.logs {
  padding-left: 20px;
  line-height: 1.8;
  color: #374151;
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