<template>
  <div class="page">
    <h1>AI 任务解析页</h1>

    <div class="card">
      <h2>输入自然语言需求</h2>
      <textarea
        v-model="inputText"
        class="input-box"
        placeholder="例如：给用户管理页面增加按手机号搜索功能，需要前后端都修改，优先级高，3天内完成，验收标准是支持回车搜索、清空按钮、无结果提示。"
      />

      <div class="actions">
        <button @click="handleParse" :disabled="loading || !inputText.trim()">
          {{ loading ? '解析中...' : '解析并保存' }}
        </button>
        <button @click="clearAll" :disabled="loading">清空</button>
        <button @click="loadRecords" :disabled="loading">刷新最近记录</button>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-text">{{ successMessage }}</p>
    </div>

    <div class="card">
      <h2>本次结构化结果</h2>
      <pre class="json-box">{{ formattedResult }}</pre>
      <div v-if="usage" class="usage-box">
        <p><strong>prompt_tokens：</strong>{{ usage.prompt_tokens }}</p>
        <p><strong>completion_tokens：</strong>{{ usage.completion_tokens }}</p>
        <p><strong>total_tokens：</strong>{{ usage.total_tokens }}</p>
      </div>
    </div>

    <div class="card">
      <h2>最近解析记录</h2>

      <div v-if="recordList.length === 0" class="empty">
        暂无记录
      </div>

      <ul v-else class="record-list">
        <li v-for="item in recordList" :key="item.id" class="record-item">
          <p><strong>ID：</strong>{{ item.id }}</p>
          <p><strong>时间：</strong>{{ item.created_at }}</p>
          <p><strong>模型：</strong>{{ item.model_name || '-' }}</p>
          <p><strong>原始需求：</strong>{{ item.source_text }}</p>
          <pre class="json-box">{{ JSON.stringify(item.result_json, null, 2) }}</pre>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { getTaskRecordsApi, parseTaskApi } from '../api/taskParser'

const inputText = ref('')
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const result = ref<any>(null)
const usage = ref<any>(null)
const recordList = ref<any[]>([])

const formattedResult = computed(() => {
  if (!result.value) {
    return '这里会显示本次解析后的 JSON 结果'
  }
  return JSON.stringify(result.value, null, 2)
})

const clearAll = () => {
  inputText.value = ''
  errorMessage.value = ''
  successMessage.value = ''
  result.value = null
  usage.value = null
}

const loadRecords = async () => {
  try {
    const res = await getTaskRecordsApi(10)
    recordList.value = res.data.items || []
  } catch (error: any) {
    console.error(error)
    errorMessage.value = '加载最近记录失败'
  }
}

const handleParse = async () => {
  const text = inputText.value.trim()
  if (!text) return

  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const res = await parseTaskApi(text)
    result.value = res.data.data
    usage.value = res.data.usage || null
    successMessage.value = `解析成功，已保存记录 #${res.data.record_id}`
    await loadRecords()
  } catch (error: any) {
    console.error(error)
    errorMessage.value =
      error?.response?.data?.detail || error?.message || '解析失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadRecords()
})
</script>

<style scoped>
.page {
  max-width: 1000px;
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
  min-height: 140px;
  padding: 12px;
  box-sizing: border-box;
  resize: vertical;
}

.actions {
  margin-top: 12px;
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

button {
  padding: 8px 16px;
  cursor: pointer;
}

.json-box {
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
  white-space: pre-wrap;
  word-break: break-word;
  overflow-x: auto;
}

.usage-box {
  margin-top: 12px;
  padding: 12px;
  background: #f5f7fa;
  border-radius: 6px;
}

.record-list {
  padding-left: 0;
  list-style: none;
}

.record-item {
  padding: 12px;
  border: 1px solid #ebeef5;
  border-radius: 6px;
  margin-bottom: 12px;
}

.error-text {
  margin-top: 12px;
  color: #d93025;
}

.success-text {
  margin-top: 12px;
  color: #2e7d32;
}

.empty {
  color: #909399;
}
</style>