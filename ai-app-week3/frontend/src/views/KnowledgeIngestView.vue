<template>
  <div class="page">
    <h1>知识文档导入页</h1>

    <div class="card">
      <h2>导入配置</h2>

      <div class="form-item">
        <label>文件名</label>
        <input v-model="filename" placeholder="例如：sample_manual.md" />
      </div>

      <div class="form-row">
        <div class="form-item">
          <label>chunk_size</label>
          <input v-model.number="chunkSize" type="number" min="100" max="2000" />
        </div>

        <div class="form-item">
          <label>overlap</label>
          <input v-model.number="overlap" type="number" min="0" max="500" />
        </div>
      </div>

      <div class="actions">
        <button @click="handleIngest" :disabled="loading || !filename.trim()">
          {{ loading ? '导入中...' : '开始导入' }}
        </button>
        <button @click="loadDocuments" :disabled="loading">刷新文档列表</button>
        <button @click="clearResult" :disabled="loading">清空结果</button>
      </div>

      <p v-if="errorMessage" class="error-text">{{ errorMessage }}</p>
      <p v-if="successMessage" class="success-text">{{ successMessage }}</p>
    </div>

    <div class="card">
      <h2>本次导入结果</h2>
      <pre class="json-box">{{ formattedResult }}</pre>
    </div>

    <div class="card">
      <h2>最近导入文档</h2>

      <div v-if="documentList.length === 0" class="empty">
        暂无导入记录
      </div>

      <ul v-else class="doc-list">
        <li v-for="item in documentList" :key="item.id" class="doc-item">
          <p><strong>ID：</strong>{{ item.id }}</p>
          <p><strong>文件名：</strong>{{ item.source_name }}</p>
          <p><strong>类型：</strong>{{ item.file_type }}</p>
          <p><strong>chunk 数：</strong>{{ item.chunk_count }}</p>
          <p><strong>时间：</strong>{{ item.created_at }}</p>

          <button @click="loadChunks(item.id)">查看 chunks</button>
        </li>
      </ul>
    </div>

    <div class="card">
      <h2>当前 chunk 列表</h2>

      <div v-if="chunkList.length === 0" class="empty">
        暂无 chunk
      </div>

      <ul v-else class="chunk-list">
        <li v-for="item in chunkList" :key="item.id" class="chunk-item">
          <p>
            <strong>chunk_index：</strong>{{ item.chunk_index }}
            <span class="muted">（{{ item.char_count }} 字符）</span>
          </p>
          <pre class="json-box">{{ item.content }}</pre>
        </li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  getKnowledgeChunksApi,
  getKnowledgeDocumentsApi,
  ingestKnowledgeApi,
} from '../api/knowledge'

const filename = ref('sample_manual.md')
const chunkSize = ref(300)
const overlap = ref(50)
const loading = ref(false)
const errorMessage = ref('')
const successMessage = ref('')
const ingestResult = ref<any>(null)
const documentList = ref<any[]>([])
const chunkList = ref<any[]>([])

const formattedResult = computed(() => {
  if (!ingestResult.value) {
    return '这里会显示本次导入结果'
  }
  return JSON.stringify(ingestResult.value, null, 2)
})

const clearResult = () => {
  errorMessage.value = ''
  successMessage.value = ''
  ingestResult.value = null
  chunkList.value = []
}

const loadDocuments = async () => {
  try {
    const res = await getKnowledgeDocumentsApi(10)
    documentList.value = res.data.items || []
  } catch (error: any) {
    console.error(error)
    errorMessage.value = '加载文档列表失败'
  }
}

const loadChunks = async (documentId: number) => {
  try {
    const res = await getKnowledgeChunksApi(documentId, 20)
    chunkList.value = res.data.items || []
  } catch (error: any) {
    console.error(error)
    errorMessage.value = '加载 chunk 列表失败'
  }
}

const handleIngest = async () => {
  if (!filename.value.trim()) return

  loading.value = true
  errorMessage.value = ''
  successMessage.value = ''

  try {
    const res = await ingestKnowledgeApi({
      filename: filename.value.trim(),
      chunk_size: chunkSize.value,
      overlap: overlap.value,
    })

    ingestResult.value = res.data
    successMessage.value = '导入成功'
    await loadDocuments()

    const latestId = res.data?.document?.id
    if (latestId) {
      await loadChunks(latestId)
    }
  } catch (error: any) {
    console.error(error)
    errorMessage.value =
      error?.response?.data?.detail || error?.message || '导入失败'
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadDocuments()
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

.form-row {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
}

.form-item {
  margin-bottom: 12px;
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.form-item input {
  padding: 8px 10px;
  min-width: 240px;
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

.doc-list,
.chunk-list {
  padding-left: 0;
  list-style: none;
}

.doc-item,
.chunk-item {
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

.empty,
.muted {
  color: #909399;
}
</style>