<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  executeAiTool,
  fetchAvailableTools,
  fetchRecentToolCallLogs,
  type ToolCallExecuteResponse,
  type ToolCallLogRecord,
  type ToolDefinitionItem,
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

const recentLogs = ref<ToolCallLogRecord[]>([])
const logsLoading = ref(false)

const availableTools = ref<ToolDefinitionItem[]>([])
const toolsLoading = ref(false)

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
    await loadRecentLogs()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '请求失败'
  } finally {
    loading.value = false
  }
}

async function loadRecentLogs() {
  logsLoading.value = true

  try {
    recentLogs.value = await fetchRecentToolCallLogs(20)
  } catch (error) {
    console.error(error)
  } finally {
    logsLoading.value = false
  }
}

async function loadAvailableTools() {
  toolsLoading.value = true

  try {
    availableTools.value = await fetchAvailableTools()
  } catch (error) {
    console.error(error)
  } finally {
    toolsLoading.value = false
  }
}

onMounted(() => {
  loadAvailableTools()
  loadRecentLogs()
})
</script>

<template>
  <div class="page">
    <h2>Tool Calling 入门：自然语言调用后端工具</h2>

    <p class="desc">输入一句自然语言，模型判断工具名和参数，后端校验后执行真实函数。</p>
    <div class="tools">
      <h3>当前可用工具白名单</h3>

      <p v-if="toolsLoading" class="meta">工具加载中...</p>

      <table v-else class="table">
        <thead>
          <tr>
            <th>工具名</th>
            <th>说明</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="tool in availableTools" :key="tool.name">
            <td>{{ tool.name }}</td>
            <td>{{ tool.description }}</td>
          </tr>

          <tr v-if="availableTools.length === 0">
            <td colspan="2">暂无可用工具</td>
          </tr>
        </tbody>
      </table>
    </div>

    <textarea v-model="inputText" class="textarea" placeholder="例如：帮我创建一个高优先级学习任务：明晚 8 点复习 RAG" />

    <div class="examples">
      <button class="small-button" @click="inputText = '帮我创建一个高优先级学习任务：明晚 8 点复习 RAG'">示例：创建任务</button>

      <button class="small-button" @click="inputText = '查看我最近 5 条任务'">示例：查看最近任务</button>
    </div>

    <button
      class="button"
      :disabled="loading"
      @click="handleExecute"
    >{{ loading ? '执行中...' : '执行工具调用' }}</button>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <div v-if="result" class="result">
      <h3>工具调用结果</h3>

      <div class="grid">
        <div class="label">日志 ID</div>
        <div>{{ result.log_id || '-' }}</div>

        <div class="label">工具名</div>
        <div>{{ result.tool_name }}</div>

        <div class="label">自动修复次数</div>
        <div>{{ result.retry_count }}</div>

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
    <div class="logs">
      <h3>最近工具调用日志</h3>

      <p v-if="logsLoading" class="meta">加载中...</p>

      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>工具</th>
            <th>状态</th>
            <th>修复次数</th>
            <th>耗时</th>
            <th>用户输入</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="item in recentLogs" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.tool_name || '-' }}</td>
            <td>{{ item.status }}</td>
            <td>{{ item.retry_count }}</td>
            <td>{{ item.elapsed_ms }} ms</td>
            <td>{{ item.source_text }}</td>
          </tr>

          <tr v-if="recentLogs.length === 0">
            <td colspan="6">暂无日志</td>
          </tr>
        </tbody>
      </table>
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
.logs {
  margin-top: 32px;
}

.meta {
  color: #666;
  margin-top: 12px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  margin-top: 12px;
}

.table th,
.table td {
  border: 1px solid #eee;
  padding: 8px;
  text-align: left;
  font-size: 14px;
  vertical-align: top;
}

.table th {
  background: #fafafa;
  font-weight: 600;
}
.tools {
  margin: 20px 0;
}
</style>