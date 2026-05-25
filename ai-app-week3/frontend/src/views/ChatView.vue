<template>
  <div class="chat-page">
    <h1>真实 LLM 流式聊天页</h1>

    <div class="card">
      <textarea
        v-model="message"
        class="input-box"
        placeholder="请输入你的问题，例如：请用 5 句话解释什么是 SSE。"
      />

      <div class="actions">
        <button @click="handleSend" :disabled="loading || !message.trim()">
          {{ loading ? '生成中...' : '发送' }}
        </button>

        <button @click="clearAll" :disabled="loading">
          清空
        </button>
      </div>
    </div>

    <div class="card">
      <h2>模型回复</h2>
      <div class="result-box">
        {{ answer || '这里会显示模型的流式回复' }}
      </div>
    </div>

    <div class="card">
      <h2>状态信息</h2>
      <p><strong>状态：</strong>{{ status }}</p>
      <p><strong>模型：</strong>{{ modelName || '-' }}</p>
      <p><strong>耗时：</strong>{{ elapsedMs ? `${elapsedMs} ms` : '-' }}</p>

      <div v-if="usage" class="usage-box">
        <p><strong>prompt_tokens：</strong>{{ usage.prompt_tokens }}</p>
        <p><strong>completion_tokens：</strong>{{ usage.completion_tokens }}</p>
        <p><strong>total_tokens：</strong>{{ usage.total_tokens }}</p>
      </div>

      <p v-if="errorMessage" class="error-text">
        {{ errorMessage }}
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { streamChatApi } from '../api/chat'

const message = ref('')
const answer = ref('')
const status = ref('未开始')
const modelName = ref('')
const elapsedMs = ref<number | null>(null)
const usage = ref<any>(null)
const errorMessage = ref('')
const loading = ref(false)

const clearAll = () => {
  message.value = ''
  answer.value = ''
  status.value = '未开始'
  modelName.value = ''
  elapsedMs.value = null
  usage.value = null
  errorMessage.value = ''
}

const handleSend = async () => {
  const text = message.value.trim()
  if (!text) return

  answer.value = ''
  status.value = '请求中'
  modelName.value = ''
  elapsedMs.value = null
  usage.value = null
  errorMessage.value = ''
  loading.value = true

  try {
    await streamChatApi(text, {
      onStart(payload) {
        status.value = '已连接，正在生成'
        modelName.value = payload.model || ''
      },
      onChunk(payload) {
        answer.value += payload.content || ''
      },
      onUsage(payload) {
        usage.value = payload.usage || null
      },
      onDone(payload) {
        status.value = '生成完成'
        elapsedMs.value = payload.elapsed_ms || null
        loading.value = false
      },
      onError(payload) {
        status.value = '生成失败'
        errorMessage.value = payload.message || '未知错误'
        loading.value = false
      },
    })
  } catch (error: any) {
    status.value = '请求失败'
    errorMessage.value = error?.message || '请求异常'
    loading.value = false
  }
}
</script>

<style scoped>
.chat-page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.card {
  margin-top: 16px;
  padding: 16px;
  border: 1px solid #dcdfe6;
  border-radius: 8px;
  background: #fff;
}

.input-box {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  box-sizing: border-box;
  resize: vertical;
}

.actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
}

button {
  padding: 8px 16px;
  cursor: pointer;
}

.result-box {
  min-height: 120px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.usage-box {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.error-text {
  margin-top: 12px;
  color: #d93025;
}
</style>