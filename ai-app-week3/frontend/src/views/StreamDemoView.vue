<template>
  <div class="stream-page">
    <h1>流式输出演示页</h1>

    <div class="card">
      <p><strong>连接状态：</strong>{{ status }}</p>

      <div class="actions">
        <button @click="startStream" :disabled="isStreaming">开始流式输出</button>
        <button @click="stopStream" :disabled="!isStreaming">关闭连接</button>
        <button @click="clearResult">清空结果</button>
      </div>
    </div>

    <div class="card">
      <h2>拼接后的完整结果</h2>
      <div class="result-box">
        {{ fullText || '这里会显示流式拼接后的文本结果' }}
      </div>
    </div>

    <div class="card">
      <h2>分段结果</h2>

      <div v-if="chunkList.length === 0" class="empty">
        还没有收到任何分段数据
      </div>

      <ul v-else class="chunk-list">
        <li v-for="item in chunkList" :key="item.id">
          <span class="index">#{{ item.index }}</span>
          <span>{{ item.content }}</span>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onBeforeUnmount } from 'vue'
import { API_BASE_URL } from '../api/http'

type ChunkItem = {
  id: number
  index: number
  content: string
}

const status = ref('未连接')
const isStreaming = ref(false)
const fullText = ref('')
const chunkList = ref<ChunkItem[]>([])

let eventSource: EventSource | null = null
let idSeed = 1

const startStream = () => {
  stopStream()
  clearResult()

  status.value = '连接中...'
  isStreaming.value = true

  eventSource = new EventSource(`${API_BASE_URL}/stream/demo`)

  eventSource.onopen = () => {
    status.value = '连接成功，正在接收数据'
  }

  eventSource.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)

      if (payload.type === 'chunk') {
        fullText.value += payload.content
        chunkList.value.push({
          id: idSeed++,
          index: payload.index,
          content: payload.content,
        })
      }

      if (payload.type === 'done') {
        status.value = '已完成'
        stopStream(false)
      }
    } catch (error) {
      console.error('解析流数据失败：', error)
      status.value = '数据解析失败'
      stopStream(false)
    }
  }

  eventSource.onerror = () => {
    if (isStreaming.value) {
      status.value = '连接异常或连接已关闭'
    }
    stopStream(false)
  }
}

const stopStream = (updateStatus = true) => {
  if (eventSource) {
    eventSource.close()
    eventSource = null
  }

  isStreaming.value = false

  if (updateStatus && status.value !== '已完成') {
    status.value = '连接已手动关闭'
  }
}

const clearResult = () => {
  fullText.value = ''
  chunkList.value = []
  idSeed = 1

  if (!isStreaming.value) {
    status.value = '未连接'
  }
}

onBeforeUnmount(() => {
  stopStream(false)
})
</script>

<style scoped>
.stream-page {
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

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  margin-top: 12px;
}

button {
  padding: 8px 16px;
  cursor: pointer;
}

.result-box {
  min-height: 80px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  line-height: 1.8;
  white-space: pre-wrap;
}

.chunk-list {
  padding-left: 20px;
}

.chunk-list li {
  margin-bottom: 8px;
  line-height: 1.6;
}

.index {
  display: inline-block;
  width: 48px;
  color: #909399;
}

.empty {
  color: #909399;
}
</style>