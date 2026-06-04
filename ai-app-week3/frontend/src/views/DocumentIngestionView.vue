<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import {
  fetchDocumentChunks,
  fetchDocumentDetail,
  fetchDocumentStats,
  fetchRecentDocuments,
  ingestTextDocument,
  rechunkDocument,
  searchDocumentChunks,
  updateDocumentChunk,
  uploadTextDocument,
  type ChunkQualityStatus,
  type DocumentChunkItem,
  type DocumentChunkSearchItem,
  type DocumentItem,
  type DocumentStatsResponse,
  type SplitStrategy,
} from '../api/documents'

const title = ref('RAG 学习笔记')
const content = ref(`# RAG 学习笔记

RAG 是 Retrieval Augmented Generation，也就是检索增强生成。

## 文档解析

文档解析的目标是把 PDF、Markdown、TXT 等资料转成干净的纯文本。

## 文本切分

文本切分会把长文档拆成多个 chunk。chunk 太大可能包含无关信息，chunk 太小可能丢失上下文。

## 向量检索

后续我们会把 chunk 转成 embedding，再存入向量库，用于相似度检索。

## 引用生成

RAG 回答不仅要生成答案，还要告诉用户答案来自哪些 chunk。`)
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

const splitStrategy = ref<SplitStrategy>('markdown_headings')
const rechunkLoading = ref(false)

const selectedFile = ref<File | null>(null)
const uploadLoading = ref(false)

const searchKeyword = ref('RAG')
const searchOnlyCurrentDocument = ref(true)
const searchLoading = ref(false)
const searchResults = ref<DocumentChunkSearchItem[]>([])
const searchMessage = ref('')

const selectedChunk = ref<DocumentChunkItem | null>(null)
const chunkEditContent = ref('')
const chunkEditActive = ref(true)
const chunkEditLoading = ref(false)
const chunkEditMessage = ref('')

const chunkEditQualityStatus = ref<ChunkQualityStatus>('unknown')
const chunkEditQualityNote = ref('')

const documentStats = ref<DocumentStatsResponse | null>(null)
const statsLoading = ref(false)

function escapeHtml(text: string) {
  return text
    .replaceAll('&', '&amp;')
    .replaceAll('<', '&lt;')
    .replaceAll('>', '&gt;')
    .replaceAll('"', '&quot;')
    .replaceAll("'", '&#039;')
}


function escapeRegExp(text: string) {
  return text.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
}


function highlightKeyword(content: string) {
  const keyword = searchKeyword.value.trim()

  if (!keyword) {
    return escapeHtml(content)
  }

  const escapedContent = escapeHtml(content)
  const pattern = new RegExp(escapeRegExp(keyword), 'gi')

  return escapedContent.replace(
    pattern,
    (matched) => `<mark>${matched}</mark>`
  )
}

async function handleSearchChunks() {
  const keyword = searchKeyword.value.trim()

  if (!keyword) {
    searchMessage.value = '请输入搜索关键词'
    return
  }

  searchLoading.value = true
  searchMessage.value = ''
  searchResults.value = []

  try {
    const documentId =
      searchOnlyCurrentDocument.value && currentDocument.value
        ? currentDocument.value.id
        : null

    searchResults.value = await searchDocumentChunks({
      keyword,
      document_id: documentId,
      limit: 20,
    })

    searchMessage.value = `找到 ${searchResults.value.length} 个匹配 chunk`
  } catch (error) {
    searchMessage.value =
      error instanceof Error ? error.message : '搜索失败'
  } finally {
    searchLoading.value = false
  }
}

function handleEditChunk(chunk: DocumentChunkItem) {
  selectedChunk.value = chunk
  chunkEditContent.value = chunk.content
  chunkEditActive.value = chunk.is_active
  chunkEditQualityStatus.value = chunk.quality_status || 'unknown'
  chunkEditQualityNote.value = chunk.quality_note || ''
  chunkEditMessage.value = ''
}


async function handleSaveChunkEdit() {
  if (!selectedChunk.value) {
    chunkEditMessage.value = '请先选择一个 chunk'
    return
  }

  if (!chunkEditContent.value.trim()) {
    chunkEditMessage.value = 'chunk 内容不能为空'
    return
  }

  chunkEditLoading.value = true
  chunkEditMessage.value = ''

  try {
    const updated = await updateDocumentChunk(selectedChunk.value.id, {
      content: chunkEditContent.value.trim(),
      is_active: chunkEditActive.value,
      quality_status: chunkEditQualityStatus.value,
      quality_note: chunkEditQualityNote.value.trim() || null,
    })

    selectedChunk.value = updated
    chunkEditContent.value = updated.content
    chunkEditActive.value = updated.is_active
    chunkEditQualityStatus.value = updated.quality_status
    chunkEditQualityNote.value = updated.quality_note || ''
    chunkEditMessage.value = '保存成功'

    if (currentDocument.value) {
      chunks.value = await fetchDocumentChunks(currentDocument.value.id)
    }
    await loadDocumentStats()

    if (searchKeyword.value.trim()) {
      await handleSearchChunks()
    }
  } catch (error) {
    chunkEditMessage.value =
      error instanceof Error ? error.message : '保存失败'
  } finally {
    chunkEditLoading.value = false
  }
}

async function loadDocumentStats() {
  statsLoading.value = true

  try {
    documentStats.value = await fetchDocumentStats()
  } catch (error) {
    console.error(error)
  } finally {
    statsLoading.value = false
  }
}

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
      split_strategy: splitStrategy.value,
    })

    currentDocument.value = result.document
    chunks.value = result.chunks

    await loadDocumentStats()
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

  try {
    const detail = await fetchDocumentDetail(document.id)
    currentDocument.value = detail

    chunkSize.value = detail.chunk_size
    chunkOverlap.value = detail.chunk_overlap

    if (
      detail.source_type === 'chars' ||
      detail.source_type === 'markdown_headings'
    ) {
      splitStrategy.value = detail.source_type
    }

    chunks.value = await fetchDocumentChunks(detail.id)
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '获取文档详情失败'
  }
}

async function handleRechunk() {
  if (!currentDocument.value) {
    errorMessage.value = '请先选择或创建一个文档'
    return
  }

  if (chunkOverlap.value >= chunkSize.value) {
    errorMessage.value = 'chunk_overlap 必须小于 chunk_size'
    return
  }

  rechunkLoading.value = true
  errorMessage.value = ''

  try {
    const result = await rechunkDocument(currentDocument.value.id, {
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value,
      split_strategy: splitStrategy.value,
    })

    currentDocument.value = result.document
    chunks.value = result.chunks

    await loadDocumentStats()
    await loadRecentDocuments()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '重新切分失败'
  } finally {
    rechunkLoading.value = false
  }
}

function handleFileChange(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0] || null

  selectedFile.value = file

  if (file && !title.value.trim()) {
    title.value = file.name
  }
}

async function handleUploadAndIngest() {
  if (!selectedFile.value) {
    errorMessage.value = '请先选择 .txt / .md / .markdown 文件'
    return
  }

  if (chunkOverlap.value >= chunkSize.value) {
    errorMessage.value = 'chunk_overlap 必须小于 chunk_size'
    return
  }

  uploadLoading.value = true
  errorMessage.value = ''
  currentDocument.value = null
  chunks.value = []

  try {
    const result = await uploadTextDocument({
      file: selectedFile.value,
      title: title.value.trim() || selectedFile.value.name,
      chunk_size: chunkSize.value,
      chunk_overlap: chunkOverlap.value,
      split_strategy: splitStrategy.value,
    })

    currentDocument.value = result.document
    chunks.value = result.chunks

    await loadRecentDocuments()
  } catch (error) {
    errorMessage.value =
      error instanceof Error ? error.message : '上传文档失败'
  } finally {
    uploadLoading.value = false
  }
}

onMounted(() => {
  loadDocumentStats()
  loadRecentDocuments()
})
</script>

<template>
  <div class="page">
    <h2>Week7 Day01：文档解析与切分</h2>

    <p class="desc">粘贴 TXT / Markdown 文档内容，后端会按 chunk_size 和 overlap 切分，并保存到数据库。</p>

    <label class="field">
      <span>文档标题</span>
      <input v-model="title" class="input" />
    </label>

    <div class="row three">
      <label class="field">
        <span>切分策略</span>
        <select v-model="splitStrategy" class="input">
          <option value="chars">按字符切分</option>
          <option value="markdown_headings">Markdown 按标题切分</option>
        </select>
      </label>

      <label class="field">
        <span>chunk_size</span>
        <input v-model.number="chunkSize" class="input" type="number" />
      </label>

      <label class="field">
        <span>chunk_overlap</span>
        <input v-model.number="chunkOverlap" class="input" type="number" />
      </label>
    </div>
    <div class="upload-panel">
      <h3>方式一：上传 TXT / Markdown 文件</h3>

      <label class="field">
        <span>选择文件</span>
        <input
          class="input"
          type="file"
          accept=".txt, .md, .markdown, text/plain, text/markdown"
          @change="handleFileChange"
        />
      </label>

      <p v-if="selectedFile" class="meta">已选择：{{ selectedFile.name }}</p>

      <button
        class="button"
        :disabled="uploadLoading || !selectedFile"
        @click="handleUploadAndIngest"
      >{{ uploadLoading ? '上传并切分中...' : '上传并切分文档' }}</button>
    </div>

    <div class="paste-panel">
      <h3>方式二：粘贴文本内容</h3>
    </div>
    <label class="field">
      <span>文档内容</span>
      <textarea v-model="content" class="textarea" />
    </label>

    <div class="actions">
      <button
        class="button"
        :disabled="loading"
        @click="handleIngest"
      >{{ loading ? '切分中...' : '解析并切分粘贴内容' }}</button>

      <button
        class="button secondary"
        :disabled="rechunkLoading || !currentDocument"
        @click="handleRechunk"
      >{{ rechunkLoading ? '重新切分中...' : '重新切分当前文档' }}</button>
    </div>
    <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

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
        <div class="label">切分策略</div>
        <div>{{ currentDocument.source_type }}</div>
      </div>
    </div>

    <div class="section">
      <h3>Chunk 关键词搜索</h3>

      <div class="search-row">
        <input
          v-model="searchKeyword"
          class="input"
          placeholder="输入关键词，例如 RAG / 检索 / chunk"
          @keyup.enter="handleSearchChunks"
        />

        <button
          class="button"
          :disabled="searchLoading"
          @click="handleSearchChunks"
        >{{ searchLoading ? '搜索中...' : '搜索 chunks' }}</button>
      </div>

      <label class="checkbox">
        <input v-model="searchOnlyCurrentDocument" type="checkbox" />
        只搜索当前文档
      </label>

      <p v-if="searchMessage" class="meta">{{ searchMessage }}</p>

      <div v-for="item in searchResults" :key="item.id" class="chunk-card search-result">
        <div class="chunk-meta">
          文档：{{ item.document_title }}
          ｜文档 ID：{{ item.document_id }}
          ｜Chunk #{{ item.chunk_index }}
          ｜字符范围：{{ item.char_start }} - {{ item.char_end }}｜质量：{{ item.quality_status }}
        </div>
        <p v-if="item.quality_note" class="meta">质量备注：{{ item.quality_note }}</p>

        <pre v-html="highlightKeyword(item.content)"></pre>
      </div>
    </div>

    <div class="section">
      <h3>Chunk 手动编辑</h3>

      <div v-if="selectedChunk" class="edit-panel">
        <p class="meta">
          当前编辑：Chunk ID {{ selectedChunk.id }}，
          #{{ selectedChunk.chunk_index }}
        </p>

        <label class="field">
          <span>Chunk 内容</span>
          <textarea v-model="chunkEditContent" class="textarea small" />
        </label>

        <label class="checkbox">
          <input v-model="chunkEditActive" type="checkbox" />
          启用该 chunk，允许参与搜索 / 后续 RAG
        </label>
        <label class="field">
          <span>质量状态</span>
          <select v-model="chunkEditQualityStatus" class="input">
            <option value="unknown">unknown：未标记</option>
            <option value="good">good：质量好</option>
            <option value="needs_review">needs_review：需要复查</option>
            <option value="bad">bad：质量差</option>
          </select>
        </label>

        <label class="field">
          <span>质量备注</span>
          <input v-model="chunkEditQualityNote" class="input" placeholder="例如：标题完整、语义清晰、适合后续检索" />
        </label>

        <button
          class="button"
          :disabled="chunkEditLoading"
          @click="handleSaveChunkEdit"
        >{{ chunkEditLoading ? '保存中...' : '保存 chunk 修改' }}</button>

        <p v-if="chunkEditMessage" class="meta">{{ chunkEditMessage }}</p>
      </div>

      <p v-else class="meta">请先在 Chunk 列表中点击“编辑”。</p>
    </div>

    <div class="section">
      <h3>Chunk 列表</h3>

      <div
        v-for="chunk in chunks"
        :key="chunk.id"
        class="chunk-card"
        :class="{ inactive: !chunk.is_active }"
      >
        <div class="chunk-meta">
          #{{ chunk.chunk_index }}
          ｜Chunk ID：{{ chunk.id }}
          ｜字符范围：{{ chunk.char_start }} - {{ chunk.char_end }}
          ｜状态：{{ chunk.is_active ? '启用' : '禁用' }}｜质量：{{ chunk.quality_status }}
        </div>
        <p v-if="chunk.quality_note" class="meta">质量备注：{{ chunk.quality_note }}</p>
        <pre>{{ chunk.content }}</pre>

        <button class="small-button" @click="handleEditChunk(chunk)">编辑</button>
      </div>

      <p v-if="chunks.length === 0" class="meta">暂无 chunks</p>

      <details v-if="chunks.length > 0">
        <summary>查看 chunks JSON</summary>
        <pre>{{ chunksJson }}</pre>
      </details>
    </div>

    <div class="stats-panel">
      <h3>知识库导入统计</h3>

      <p v-if="statsLoading" class="meta">统计加载中...</p>

      <div v-else-if="documentStats" class="stats-grid">
        <div class="stat-card">
          <div class="stat-label">文档总数</div>
          <div class="stat-value">{{ documentStats.total_documents }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">Chunk 总数</div>
          <div class="stat-value">{{ documentStats.total_chunks }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">启用 Chunk</div>
          <div class="stat-value">{{ documentStats.active_chunks }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">禁用 Chunk</div>
          <div class="stat-value">{{ documentStats.inactive_chunks }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">good</div>
          <div class="stat-value">{{ documentStats.quality_counts.good || 0 }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">needs_review</div>
          <div class="stat-value">{{ documentStats.quality_counts.needs_review || 0 }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">bad</div>
          <div class="stat-value">{{ documentStats.quality_counts.bad || 0 }}</div>
        </div>

        <div class="stat-card">
          <div class="stat-label">平均 Chunk / 文档</div>
          <div class="stat-value">{{ documentStats.average_chunks_per_document }}</div>
        </div>
      </div>

      <p v-if="documentStats?.latest_document" class="meta">
        最近文档：#{{ documentStats.latest_document.id }}
        {{ documentStats.latest_document.title }}
      </p>
    </div>

    <div class="section">
      <h3>最近文档</h3>

      <p v-if="recentLoading" class="meta">加载中...</p>

      <table v-else class="table">
        <thead>
          <tr>
            <th>ID</th>
            <th>标题</th>
            <th>Chunk 数量</th>
            <th>切分策略</th>
            <th>切分参数</th>
            <th>操作</th>
          </tr>
        </thead>

        <tbody>
          <tr v-for="doc in recentDocuments" :key="doc.id">
            <td>{{ doc.id }}</td>
            <td>{{ doc.title }}</td>
            <td>{{ doc.chunk_count }}</td>
            <td>{{ doc.source_type }}</td>
            <td>{{ doc.chunk_size }} / {{ doc.chunk_overlap }}</td>
            <td>
              <button class="small-button" @click="handleViewChunks(doc)">查看 chunks</button>
            </td>
          </tr>

          <tr v-if="recentDocuments.length === 0">
            <td colspan="6">暂无文档</td>
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

.row.three {
  grid-template-columns: 1fr 1fr 1fr;
}

.actions {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
}

.button.secondary {
  background: #fff;
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

.upload-panel,
.paste-panel {
  margin-top: 20px;
  padding-top: 16px;
  border-top: 1px solid #eee;
}
.search-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.search-row .input {
  flex: 1;
}

.checkbox {
  display: inline-flex;
  gap: 6px;
  align-items: center;
  margin-top: 12px;
  color: #555;
}

.search-result {
  border-left: 4px solid #333;
}

:deep(mark) {
  padding: 0 2px;
  border-radius: 2px;
  background: #fff3a3;
}
.chunk-card.inactive {
  opacity: 0.55;
  background: #fafafa;
}

.edit-panel {
  border: 1px solid #eee;
  padding: 16px;
  background: #fff;
}

.textarea.small {
  min-height: 120px;
}

.stats-panel {
  margin-top: 20px;
  padding: 16px;
  border: 1px solid #eee;
  background: #fff;
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.stat-card {
  padding: 12px;
  border: 1px solid #eee;
  background: #fafafa;
}

.stat-label {
  color: #666;
  font-size: 13px;
  margin-bottom: 6px;
}

.stat-value {
  font-size: 22px;
  font-weight: 700;
}
</style>