<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  extractTaskFromText,
  type StructuredTask,
} from '../api/structured'

const inputText = ref(
  '明天下午 3 点提醒我复习 FastAPI，优先级高，分类是学习'
)

const loading = ref(false)
const errorMessage = ref('')
const task = ref<StructuredTask | null>(null)
const rawText = ref('')
const elapsedMs = ref<number | null>(null)

const resultJson = computed(() => {
  if (!task.value) return ''
  return JSON.stringify(task.value, null, 2)
})

async function handleExtract() {
  const text = inputText.value.trim()

  if (!text) {
    errorMessage.value = '请输入任务描述'
    return
  }

  loading.value = true
  errorMessage.value = ''
  task.value = null
  rawText.value = ''
  elapsedMs.value = null

  try {
    const result = await extractTaskFromText(text)
    task.value = result.data
    rawText.value = result.raw_text
    elapsedMs.value = result.elapsed_ms
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '请求失败'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="page">
    <h2>AI 表单助手 v1：任务结构化抽取</h2>

    <p class="desc">
      输入一句自然语言，让模型返回固定 JSON，并由后端 Pydantic 校验。
    </p>

    <textarea
      v-model="inputText"
      class="textarea"
      placeholder="例如：明天下午 3 点提醒我复习 FastAPI，优先级高，分类是学习"
    />

    <button class="button" :disabled="loading" @click="handleExtract">
      {{ loading ? '抽取中...' : '抽取结构化任务' }}
    </button>

    <p v-if="errorMessage" class="error">
      {{ errorMessage }}
    </p>

    <div v-if="task" class="result">
      <h3>结构化结果</h3>

      <div class="grid">
        <div class="label">标题</div>
        <div>{{ task.title }}</div>

        <div class="label">分类</div>
        <div>{{ task.category }}</div>

        <div class="label">优先级</div>
        <div>{{ task.priority }}</div>

        <div class="label">时间</div>
        <div>{{ task.due_time || '-' }}</div>

        <div class="label">描述</div>
        <div>{{ task.description || '-' }}</div>
      </div>

      <p v-if="elapsedMs !== null" class="meta">
        耗时：{{ elapsedMs }} ms
      </p>

      <h3>后端校验后的 JSON</h3>
      <pre>{{ resultJson }}</pre>

      <h3>模型原始返回</h3>
      <pre>{{ rawText }}</pre>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 900px;
  margin: 0 auto;
  padding: 24px;
}

.desc {
  color: #666;
  margin-bottom: 16px;
}

.textarea {
  width: 100%;
  min-height: 120px;
  padding: 12px;
  box-sizing: border-box;
  resize: vertical;
  font-size: 14px;
}

.button {
  margin-top: 12px;
  padding: 8px 16px;
  cursor: pointer;
}

.button:disabled {
  cursor: not-allowed;
  opacity: 0.6;
}

.error {
  margin-top: 12px;
  color: #c0392b;
}

.result {
  margin-top: 24px;
}

.grid {
  display: grid;
  grid-template-columns: 120px 1fr;
  border: 1px solid #eee;
}

.grid > div {
  padding: 10px;
  border-bottom: 1px solid #eee;
}

.label {
  font-weight: 600;
  background: #fafafa;
}

.meta {
  color: #666;
  margin-top: 12px;
}

pre {
  background: #f7f7f7;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
}
</style>