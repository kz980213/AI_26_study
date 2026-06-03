<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  fetchDocumentChunks,
  fetchRecentDocuments,
  ingestTextDocument,
  type DocumentChunkItem,
  type DocumentItem,
} from '../api/documents'

const title = ref('RAG 学习笔记')
const content = ref(`RAG 是 Retrieval Augmented Generation，也就是检索增强生成。

一个最小 RAG 系统通常包含：文档解析、文本切分、向量化、向量检索、上下文组装、模型生成和引用展示。

文档切分非常重要。如果 chunk 太大，可能包含太多无关信息；如果 chunk 太小，可能丢失上下文。后续我们会继续学习 chunk_size、overlap、metadata 对召回效果的影响。`)

const chunkSize = ref(200)
const chunkOverlap = ref(30)

const loading = ref(false)
const errorMessage = ref('')
const currentDocument = ref<DocumentItem | null>(null)
const chunks = ref<DocumentChunkItem[]>([])

const recentDocuments = ref<DocumentItem[]>([])
const recentLoading = ref(false)

const chunksJson = computed(() => {
  return JSON.stringify(chunks.value, null, 2)
})

async function loadRecentDocuments() {
  recentLoading.value = true

  try {
    recentDocuments.value = await fetchRecentDocuments(20)
  } catch (error) {
    console.error(error)
  } finally {
    recentLoading.value = false
  }
}

async function handleIngest() {
  if (!title.value.trim()) {
    errorMessage.value = '请输入文档标题'
    return
  }

  if (!content.value.trim()) {
    errorMessage.value = '请输入文档内容'
    return
  }

  if (chunkOverlap.value >= chunkSize.value) {
    errorMessage.value = 'chunk_overlap 必须小于 chunk_size'
    return
  }

  loading.value = true
  errorMessage.value = ''
  currentDocument.value = null
  chunks.value = []

  try {
    const result = await ingestTextDocument({
      title: title.value.trim(),
      content: content.value.trim(),
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value,
    })

    currentDocument.value = result.document
    chunks.value = result.chunks

    await loadRecentDocuments()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '文档解析失败'
  } finally {
    loading.value = false
  }
}

async function handleViewChunks(document: DocumentItem) {
  errorMessage.value = ''
  currentDocument.value = document

  try {
    chunks.value = await fetchDocumentChunks(document.id)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '获取 chunks 失败'
  }
}

onMounted(() => {
  loadRecentDocuments()
})
</script>

<template>
  <div class="page">
    <h2>Week7 Day01：文档解析与切分</h2>

    <p class="desc">
      粘贴 TXT / Markdown 文档内容，后端会按 chunk_size 和 overlap 切分，并保存到数据库。
    </p>

    <label class="field">
      <span>文档标题</span>
      <input v-model="title" class="input" />
    </label>

    <div class="row">
      <label class="field">
        <span>chunk_size</span>
        <input v-model.number="chunkSize" class="input" type="number" />
      </label>

      <label class="field">
        <span>chunk_overlap</span>
        <input v-model.number="chunkOverlap" class="input" type="number" />
      </label>
    </div>

    <label class="field">
      <span>文档内容</span>
      <textarea v-model="content" class="textarea" />
    </label>

    <button class="button" :disabled="loading" @click="handleIngest">
      {{ loading ? '切分中...' : '解析并切分文档' }}
    </button>

    <p v-if="errorMessage" class="error">
      {{ errorMessage }}
    </p>

    <div v-if="currentDocument" class="result">
      <h3>当前文档</h3>

      <div class="grid">
        <div class="label">文档 ID</div>
        <div>{{ currentDocument.id }}</div>

        <div class="label">标题</div>
        <div>{{ currentDocument.title }}</div>

        <div class="label">chunk 数量</div>
        <div>{{ currentDocument.chunk_count }}</div>

        <div class="label">chunk_size</div>
        <div>{{ currentDocument.chunk_size }}</div>

        <div class="label">chunk_overlap</div>
        <div>{{ currentDocument.chunk_overlap }}</div>
      </div>
    </div>

    <div class="section">
      <h3>Chunk 列表</h3>

      <div v-for="chunk in chunks" :key="chunk.id" class="chunk-card">
        <div class="chunk-meta">
          #{{ chunk.chunk_index }}
          ｜字符范围：{{ chunk.char_start }} - {{ chunk.char_end }}
        </div>

        <pre>{{ chunk.content }}</pre>
      </div>

      <p v-if="chunks.length === 0" class="meta">
        暂无 chunks
      </p>

      <details v-if="chunks.length > 0">
        <summary>查看 chunks JSON</summary>
        <pre>{{ chunksJson }}</pre>
      </details>
    </div>

    <div class="section">
      <h3>最近文档</h3>

      <p v-if="recentLoading" class="meta">
        加载中...
      </p>

      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>Chunk 数量</th>
            <th>切分参数</th>
            <th>操作</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="doc in recentDocuments" :key="doc.id">
            <td>{{ doc.id }}</td>
            <td>{{ doc.title }}</td>
            <td>{{ doc.chunk_count }}</td>
            <td>
              {{ doc.chunk_size }} / {{ doc.chunk_overlap }}
            </td>
            <td>
              <button class="small-button" @click="handleViewChunks(doc)">
                查看 chunks
              </button>
            </td>
          </tr>

          <tr v-if="recentDocuments.length === 0">
            <td colspan="5">暂无文档</td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 1000px;
  margin: 0 auto;
  padding: 24px;
}

.desc {
  color: #666;
  margin-bottom: 16px;
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

.row {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;
}

.input {
  width: 100%;
  box-sizing: border-box;
  padding: 8px;
  font-size: 14px;
}

.textarea {
  width: 100%;
  min-height: 180px;
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

.small-button {
  padding: 4px 8px;
  cursor: pointer;
}

.error {
  margin-top: 12px;
  color: #c0392b;
}

.result,
.section {
  margin-top: 28px;
}

.grid {
  display: grid;
  grid-template-columns: 140px 1fr;
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

.chunk-card {
  border: 1px solid #eee;
  padding: 12px;
  margin-bottom: 12px;
  background: #fff;
}

.chunk-meta {
  color: #666;
  margin-bottom: 8px;
  font-size: 13px;
}

pre {
  background: #f7f7f7;
  padding: 12px;
  overflow: auto;
  white-space: pre-wrap;
}

.meta {
  color: #666;
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
</style>