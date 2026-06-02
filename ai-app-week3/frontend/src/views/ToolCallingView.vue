<script setup lang="ts">
import { computed, ref } from 'vue'
import {
  executeAiTool,
  type ToolCallExecuteResponse,
} from '../api/toolCalling'

const inputText = ref(
  '帮我创建一个高优先级学习任务：明晚 8 点复习 RAG'
)

const loading = ref(false)
const errorMessage = ref('')
const result = ref<ToolCallExecuteResponse | null>(null)

const argumentsJson = computed(() => {
  if (!result.value) return ''
  return JSON.stringify(result.value.arguments, null, 2)
})

const toolResultJson = computed(() => {
  if (!result.value) return ''
  return JSON.stringify(result.value.tool_result, null, 2)
})

async function handleExecute() {
  const text = inputText.value.trim()

  if (!text) {
    errorMessage.value = '请输入自然语言指令'
    return
  }

  loading.value = true
  errorMessage.value = ''
  result.value = null

  try {
    result.value = await executeAiTool(text)
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
    <h2>Tool Calling 入门：自然语言调用后端工具</h2>

    <p class="desc">
      输入一句自然语言，模型判断工具名和参数，后端校验后执行真实函数。
    </p>

    <textarea
      v-model="inputText"
      class="textarea"
      placeholder="例如：帮我创建一个高优先级学习任务：明晚 8 点复习 RAG"
    />

    <div class="examples">
      <button
        class="small-button"
        @click="inputText = '帮我创建一个高优先级学习任务：明晚 8 点复习 RAG'"
      >
        示例：创建任务
      </button>

      <button
        class="small-button"
        @click="inputText = '查看我最近 5 条任务'"
      >
        示例：查看最近任务
      </button>
    </div>

    <button class="button" :disabled="loading" @click="handleExecute">
      {{ loading ? '执行中...' : '执行工具调用' }}
    </button>

    <p v-if="errorMessage" class="error">
      {{ errorMessage }}
    </p>

    <div v-if="result" class="result">
      <h3>工具调用结果</h3>

      <div class="grid">
        <div class="label">工具名</div>
        <div>{{ result.tool_name }}</div>

        <div class="label">耗时</div>
        <div>{{ result.elapsed_ms }} ms</div>
      </div>

      <h3>工具参数</h3>
      <pre>{{ argumentsJson }}</pre>

      <h3>工具执行结果</h3>
      <pre>{{ toolResultJson }}</pre>

      <h3>模型原始返回</h3>
      <pre>{{ result.raw_text }}</pre>
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

.examples {
  margin-top: 12px;
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
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

.small-button {
  padding: 6px 10px;
  cursor: pointer;
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

pre {
  background: #f7f7f7;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
}
</style>