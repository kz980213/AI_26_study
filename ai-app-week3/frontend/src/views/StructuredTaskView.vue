<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import {
  extractTaskFromText,
  fetchRecentStructuredTasks,
  fetchStructuredTaskDetail,
  updateStructuredTask,
  type StructuredTask,
  type StructuredTaskRecord,
  type StructuredTaskUpdatePayload,
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

const retryCount = ref<number | null>(null)

const recordId = ref<number | null>(null)
const createdAt = ref<string | null>(null)
const recentTasks = ref<StructuredTaskRecord[]>([])
const recentLoading = ref(false)

const selectedRecord = ref<StructuredTaskRecord | null>(null)
const editLoading = ref(false)
const saveLoading = ref(false)
const editMessage = ref('')

const editForm = reactive<StructuredTaskUpdatePayload>({
  title: '',
  category: '',
  priority: 'medium',
  due_time: '',
  description: '',
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
  retryCount.value = null
  recordId.value = null
  createdAt.value = null

  try {
    const result = await extractTaskFromText(text)
    task.value = result.data
    rawText.value = result.raw_text
    elapsedMs.value = result.elapsed_ms
    retryCount.value = result.retry_count
    recordId.value = result.id || null
    createdAt.value = result.created_at || null

    await loadRecentTasks()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '请求失败'
  } finally {
    loading.value = false
  }
}

async function loadRecentTasks() {
  recentLoading.value = true

  try {
    recentTasks.value = await fetchRecentStructuredTasks(20)
  } catch (error) {
    console.error(error)
  } finally {
    recentLoading.value = false
  }
}

async function handleEditRecord(record: StructuredTaskRecord) {
  editLoading.value = true
  editMessage.value = ''

  try {
    const detail = await fetchStructuredTaskDetail(record.id)

    selectedRecord.value = detail

    editForm.title = detail.title
    editForm.category = detail.category
    editForm.priority = detail.priority
    editForm.due_time = detail.due_time || ''
    editForm.description = detail.description || ''
  } catch (error) {
    editMessage.value =
      error instanceof Error ? error.message : '加载详情失败'
  } finally {
    editLoading.value = false
  }
}


async function handleSaveCorrection() {
  if (!selectedRecord.value) {
    editMessage.value = '请先选择一条记录'
    return
  }

  if (!editForm.title.trim()) {
    editMessage.value = '标题不能为空'
    return
  }

  if (!editForm.category.trim()) {
    editMessage.value = '分类不能为空'
    return
  }

  saveLoading.value = true
  editMessage.value = ''

  try {
    const updated = await updateStructuredTask(
      selectedRecord.value.id,
      {
        title: editForm.title.trim(),
        category: editForm.category.trim(),
        priority: editForm.priority,
        due_time: editForm.due_time?.trim() || null,
        description: editForm.description?.trim() || null,
      }
    )

    selectedRecord.value = updated
    editMessage.value = '保存成功'

    await loadRecentTasks()

    if (recordId.value === updated.id && task.value) {
      task.value = {
        title: updated.title,
        category: updated.category,
        priority: updated.priority,
        due_time: updated.due_time,
        description: updated.description,
      }
    }
  } catch (error) {
    editMessage.value =
      error instanceof Error ? error.message : '保存失败'
  } finally {
    saveLoading.value = false
  }
}

onMounted(() => {
  loadRecentTasks()
})
</script>

<template>
  <div class="page">
    <h2>AI 表单助手 v1：任务结构化抽取</h2>

    <p class="desc">输入一句自然语言，让模型返回固定 JSON，并由后端 Pydantic 校验。</p>

    <textarea
      v-model="inputText"
      class="textarea"
      placeholder="例如：明天下午 3 点提醒我复习 FastAPI，优先级高，分类是学习"
    />

    <button
      class="button"
      :disabled="loading"
      @click="handleExtract"
    >{{ loading ? '抽取中...' : '抽取结构化任务' }}</button>

    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

    <div class="recent">
      <h3>最近抽取记录</h3>

      <p v-if="recentLoading" class="meta">加载中...</p>

      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>分类</th>
            <th>优先级</th>
            <th>时间</th>
            <th>修复次数</th>
            <th>操作</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="item in recentTasks" :key="item.id">
            <td>{{ item.id }}</td>
            <td>{{ item.title }}</td>
            <td>{{ item.category }}</td>
            <td>{{ item.priority }}</td>
            <td>{{ item.due_time || '-' }}</td>
            <td>{{ item.retry_count }}</td>
            <td>
              <button class="small-button" @click="handleEditRecord(item)">编辑</button>
            </td>
          </tr>

          <tr v-if="recentTasks.length === 0">
            <td colspan="7">暂无记录</td>
          </tr>
        </tbody>
      </table>
    </div>

    <div class="edit-panel">
      <h3>人工修正</h3>

      <p v-if="editLoading" class="meta">正在加载详情...</p>

      <div v-if="selectedRecord" class="edit-card">
        <p class="meta">当前编辑记录 ID：{{ selectedRecord.id }}</p>

        <label class="field">
          <span>标题</span>
          <input v-model="editForm.title" class="input" />
        </label>

        <label class="field">
          <span>分类</span>
          <input v-model="editForm.category" class="input" />
        </label>

        <label class="field">
          <span>优先级</span>
          <select v-model="editForm.priority" class="input">
            <option value="low">low</option>
            <option value="medium">medium</option>
            <option value="high">high</option>
          </select>
        </label>

        <label class="field">
          <span>时间</span>
          <input v-model="editForm.due_time" class="input" />
        </label>

        <label class="field">
          <span>描述</span>
          <textarea v-model="editForm.description" class="textarea small" />
        </label>

        <button
          class="button"
          :disabled="saveLoading"
          @click="handleSaveCorrection"
        >{{ saveLoading ? '保存中...' : '保存人工修正' }}</button>
      </div>

      <p v-else class="meta">请先在最近记录中点击“编辑”。</p>

      <p v-if="editMessage" class="meta">{{ editMessage }}</p>
    </div>

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

      <p v-if="elapsedMs !== null" class="meta">耗时：{{ elapsedMs }} ms</p>
      <p v-if="retryCount !== null" class="meta">重试次数：{{ retryCount }}</p>
      <p v-if="recordId !== null" class="meta">保存记录 ID：{{ recordId }}</p>

      <p v-if="createdAt" class="meta">保存时间：{{ createdAt }}</p>

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
.recent {
  margin-top: 32px;
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
}

.table th {
  background: #fafafa;
  font-weight: 600;
}
.small-button {
  padding: 4px 8px;
  cursor: pointer;
}

.edit-panel {
  margin-top: 32px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}

.edit-card {
  border: 1px solid #eee;
  padding: 16px;
  background: #fff;
}

.field {
  display: block;
  margin-bottom: 12px;
}

.field span {
  display: block;
  margin-bottom: 6px;
  font-weight: 600;
}

.input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px;
  font-size: 14px;
}

.textarea.small {
  min-height: 80px;
}
</style>