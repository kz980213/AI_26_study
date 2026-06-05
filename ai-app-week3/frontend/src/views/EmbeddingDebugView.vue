<script setup lang="ts">
import {ref, computed} from "vue";
import {
  createChunkEmbedding,
  getChunkEmbedding,
  createDocumentChunkEmbeddings,
  searchChunkEmbeddings,
  type ChunkEmbeddingResponse,
  type BatchDocumentEmbeddingResponse,
  type EmbeddingSearchResponse,
} from "../api/embeddings";

const chunkId = ref<number | null>(null);
const loading = ref(false);
const errorMessage = ref("");
const result = ref<ChunkEmbeddingResponse | null>(null);

const documentId = ref<number | null>(null);
const skipExisting = ref(true);
const batchLoading = ref(false);
const batchErrorMessage = ref("");
const batchResult = ref<BatchDocumentEmbeddingResponse | null>(null);

const searchQuery = ref("");
const searchTopK = ref(5);
const searchDocumentId = ref<number | null>(null);
const searchOnlyActive = ref(true);
const searchLoading = ref(false);
const searchErrorMessage = ref("");
const searchResult = ref<EmbeddingSearchResponse | null>(null);

const previewEmbedding = computed(() => {
  if (!result.value?.embedding) return [];
  return result.value.embedding.slice(0, 10);
});

const searchQualityStatus = ref("");
const searchScoreThreshold = ref<number | null>(null);

async function handleCreateEmbedding() {
  if (!chunkId.value) {
    errorMessage.value = "请先输入 chunk_id";
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  result.value = null;

  try {
    const res = await createChunkEmbedding(chunkId.value);
    result.value = res;
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail || error?.message || "生成 embedding 失败";
  } finally {
    loading.value = false;
  }
}

async function handleGetEmbedding() {
  if (!chunkId.value) {
    errorMessage.value = "请先输入 chunk_id";
    return;
  }

  loading.value = true;
  errorMessage.value = "";
  result.value = null;

  try {
    const res = await getChunkEmbedding(chunkId.value);
    result.value = res;
  } catch (error: any) {
    errorMessage.value =
      error?.response?.data?.detail || error?.message || "查询 embedding 失败";
  } finally {
    loading.value = false;
  }
}

async function handleCreateDocumentEmbeddings() {
  if (!documentId.value) {
    batchErrorMessage.value = "请先输入 document_id";
    return;
  }

  batchLoading.value = true;
  batchErrorMessage.value = "";
  batchResult.value = null;

  try {
    const res = await createDocumentChunkEmbeddings(
      documentId.value,
      skipExisting.value
    );
    batchResult.value = res;
  } catch (error: any) {
    batchErrorMessage.value =
      error?.message || "批量生成文档 embeddings 失败";
  } finally {
    batchLoading.value = false;
  }
}
async function handleSearchEmbeddings() {
  if (!searchQuery.value.trim()) {
    searchErrorMessage.value = "请先输入 query";
    return;
  }

  searchLoading.value = true;
  searchErrorMessage.value = "";
  searchResult.value = null;

  try {
    const res = await searchChunkEmbeddings({
      query: searchQuery.value.trim(),
      top_k: searchTopK.value || 5,
      document_id: searchDocumentId.value || null,
      only_active: searchOnlyActive.value,
      quality_status: searchQualityStatus.value || null,
      score_threshold:
        searchScoreThreshold.value === null ||
        searchScoreThreshold.value === undefined
          ? null
          : searchScoreThreshold.value,
    });

    searchResult.value = res;
  } catch (error: any) {
    searchErrorMessage.value = error?.message || "向量检索失败";
  } finally {
    searchLoading.value = false;
  }
}
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div>
        <p class="eyebrow">Week8 Day01</p>
        <h1>Embedding 验证页</h1>
        <p class="desc">输入一个 active chunk_id，生成 embedding 并保存入库，或查询已生成的 embedding。</p>
      </div>
    </header>

    <section class="card">
      <label class="label">Chunk ID</label>

      <div class="input-row">
        <input
          v-model.number="chunkId"
          class="input"
          type="number"
          min="1"
          placeholder="请输入已有的 active chunk_id，例如 1"
        />

        <button
          class="btn primary"
          :disabled="loading"
          @click="handleCreateEmbedding"
        >{{ loading ? "处理中..." : "生成 Embedding" }}</button>

        <button class="btn" :disabled="loading" @click="handleGetEmbedding">查询 Embedding</button>
      </div>

      <p class="tip">提示：chunk_id 可以从 Week7 的文档详情页、chunk 搜索接口或数据库中获取。</p>
    </section>

    <section class="card">
      <div class="section-title">
        <div>
          <p class="eyebrow">Week8 Day02</p>
          <h2>文档 Chunks 批量 Embedding</h2>
          <p class="desc">输入 document_id，一键给这篇文档下所有 active chunks 生成 embedding。</p>
        </div>
      </div>

      <label class="label">Document ID</label>

      <div class="input-row">
        <input
          v-model.number="documentId"
          class="input"
          type="number"
          min="1"
          placeholder="请输入已有的 document_id，例如 1"
        />

        <label class="checkbox">
          <input v-model="skipExisting" type="checkbox" />
          跳过已生成
        </label>

        <button
          class="btn primary"
          :disabled="batchLoading"
          @click="handleCreateDocumentEmbeddings"
        >{{ batchLoading ? "批量处理中..." : "一键生成文档 Embeddings" }}</button>
      </div>

      <p class="tip">建议默认勾选“跳过已生成”，避免重复生成同一个 chunk 的 embedding。</p>
    </section>

    <section class="card">
      <div class="section-title">
        <p class="eyebrow">Week8 Day04</p>
        <h2>召回调试面板</h2>
        <p class="desc">输入 query 后，可通过 document_id、quality_status、score_threshold 控制召回范围。</p>
      </div>

      <label class="label">Query</label>

      <textarea v-model="searchQuery" class="textarea" rows="4" placeholder="例如：什么是文档切分？" />

      <div class="input-row search-row">
        <div class="field">
          <label class="label">TopK</label>
          <input v-model.number="searchTopK" class="input" type="number" min="1" max="20" />
        </div>

        <div class="field">
          <label class="label">Document ID</label>
          <input
            v-model.number="searchDocumentId"
            class="input"
            type="number"
            min="1"
            placeholder="不填则全部"
          />
        </div>

        <div class="field">
          <label class="label">Quality</label>
          <select v-model="searchQualityStatus" class="input">
            <option value>全部</option>
            <option value="unknown">unknown</option>
            <option value="good">good</option>
            <option value="needs_review">needs_review</option>
            <option value="bad">bad</option>
          </select>
        </div>

        <div class="field">
          <label class="label">Score 阈值</label>
          <input
            v-model.number="searchScoreThreshold"
            class="input"
            type="number"
            min="0"
            max="1"
            step="0.01"
            placeholder="例如 0.3"
          />
        </div>

        <label class="checkbox">
          <input v-model="searchOnlyActive" type="checkbox" />
          只检索 active chunks
        </label>

        <button
          class="btn primary"
          :disabled="searchLoading"
          @click="handleSearchEmbeddings"
        >{{ searchLoading ? "检索中..." : "向量检索" }}</button>
      </div>

      <p class="tip">说明：score_threshold 用来过滤低相似度结果。今天仍使用 mock embedding，重点验证召回控制流程。</p>
    </section>

    <section v-if="searchResult" class="card result-card">
      <div class="result-header">
        <h2>召回调试结果</h2>
        <span class="status">returned: {{ searchResult.returned_count }}</span>
      </div>

      <div class="grid">
        <div class="item">
          <span class="key">候选数量</span>
          <span class="value">{{ searchResult.total_candidates }}</span>
        </div>

        <div class="item">
          <span class="key">分数过滤后</span>
          <span class="value">{{ searchResult.matched_after_score_filter }}</span>
        </div>

        <div class="item">
          <span class="key">返回数量</span>
          <span class="value">{{ searchResult.returned_count }}</span>
        </div>

        <div class="item">
          <span class="key">Max Score</span>
          <span class="value">{{ searchResult.max_score ?? "-" }}</span>
        </div>

        <div class="item">
          <span class="key">Min Score</span>
          <span class="value">{{ searchResult.min_score ?? "-" }}</span>
        </div>

        <div class="item">
          <span class="key">Quality Filter</span>
          <span class="value">{{ searchResult.quality_status ?? "全部" }}</span>
        </div>
      </div>

      <div class="embedding-preview">
        <h3>Applied Filters</h3>
        <pre>{{ searchResult.applied_filters }}</pre>
      </div>

      <div class="embedding-preview">
        <h3>召回明细</h3>

        <table class="table">
          <thead>
            <tr>
              <th>排名</th>
              <th>Score</th>
              <th>Chunk ID</th>
              <th>Document ID</th>
              <th>Active</th>
              <th>Status</th>
              <th>Quality</th>
              <th>内容预览</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="(item, index) in searchResult.results" :key="item.chunk_id">
              <td>{{ index + 1 }}</td>
              <td>{{ item.score }}</td>
              <td>{{ item.chunk_id }}</td>
              <td>{{ item.document_id ?? "-" }}</td>
              <td>{{ item.is_active }}</td>
              <td>{{ item.status ?? "-" }}</td>
              <td>{{ item.quality_status ?? "-" }}</td>
              <td>{{ item.content_preview }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="embedding-preview">
        <h3>完整返回 JSON</h3>
        <pre>{{ searchResult }}</pre>
      </div>
    </section>

    <section v-if="searchErrorMessage" class="error-card">{{ searchErrorMessage }}</section>

    <section v-if="searchResult" class="card result-card">
      <div class="result-header">
        <h2>TopK 检索结果</h2>
        <span class="status">candidates: {{ searchResult.total_candidates }}</span>
      </div>

      <div class="grid">
        <div class="item">
          <span class="key">Query</span>
          <span class="value">{{ searchResult.query }}</span>
        </div>

        <div class="item">
          <span class="key">TopK</span>
          <span class="value">{{ searchResult.top_k }}</span>
        </div>

        <div class="item">
          <span class="key">候选数量</span>
          <span class="value">{{ searchResult.total_candidates }}</span>
        </div>

        <div class="item">
          <span class="key">结果数量</span>
          <span class="value">{{ searchResult.results.length }}</span>
        </div>
      </div>

      <div class="embedding-preview">
        <h3>召回明细</h3>

        <table class="table">
          <thead>
            <tr>
              <th>排名</th>
              <th>Score</th>
              <th>Chunk ID</th>
              <th>Document ID</th>
              <th>Quality</th>
              <th>内容预览</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="(item, index) in searchResult.results" :key="item.chunk_id">
              <td>{{ index + 1 }}</td>
              <td>{{ item.score }}</td>
              <td>{{ item.chunk_id }}</td>
              <td>{{ item.document_id ?? "-" }}</td>
              <td>{{ item.quality_status ?? "-" }}</td>
              <td>{{ item.content_preview }}</td>
            </tr>
          </tbody>
        </table>
      </div>

      <div class="embedding-preview">
        <h3>完整返回 JSON</h3>
        <pre>{{ searchResult }}</pre>
      </div>
    </section>

    <section v-if="batchErrorMessage" class="error-card">{{ batchErrorMessage }}</section>

    <section v-if="batchResult" class="card result-card">
      <div class="result-header">
        <h2>批量生成结果</h2>
        <span class="status">document_id: {{ batchResult.document_id }}</span>
      </div>

      <div class="grid">
        <div class="item">
          <span class="key">Active Chunks</span>
          <span class="value">{{ batchResult.total_active_chunks }}</span>
        </div>

        <div class="item">
          <span class="key">成功数</span>
          <span class="value">{{ batchResult.success_count }}</span>
        </div>

        <div class="item">
          <span class="key">跳过数</span>
          <span class="value">{{ batchResult.skipped_count }}</span>
        </div>

        <div class="item">
          <span class="key">失败数</span>
          <span class="value">{{ batchResult.failed_count }}</span>
        </div>
      </div>

      <div class="embedding-preview">
        <h3>处理明细</h3>

        <table class="table">
          <thead>
            <tr>
              <th>Chunk ID</th>
              <th>状态</th>
              <th>Embedding ID</th>
              <th>Dimension</th>
              <th>消息</th>
            </tr>
          </thead>

          <tbody>
            <tr v-for="item in batchResult.items" :key="item.chunk_id">
              <td>{{ item.chunk_id }}</td>
              <td>{{ item.status }}</td>
              <td>{{ item.embedding_id ?? "-" }}</td>
              <td>{{ item.dimension ?? "-" }}</td>
              <td>{{ item.message }}</td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>

    <section v-if="errorMessage" class="error-card">{{ errorMessage }}</section>

    <section v-if="result" class="card result-card">
      <div class="result-header">
        <h2>Embedding 结果</h2>
        <span class="status">{{ result.status }}</span>
      </div>

      <div class="grid">
        <div class="item">
          <span class="key">记录 ID</span>
          <span class="value">{{ result.id }}</span>
        </div>

        <div class="item">
          <span class="key">Chunk ID</span>
          <span class="value">{{ result.chunk_id }}</span>
        </div>

        <div class="item">
          <span class="key">Provider</span>
          <span class="value">{{ result.provider }}</span>
        </div>

        <div class="item">
          <span class="key">Model</span>
          <span class="value">{{ result.model }}</span>
        </div>

        <div class="item">
          <span class="key">Dimension</span>
          <span class="value">{{ result.dimension }}</span>
        </div>

        <div class="item">
          <span class="key">向量长度</span>
          <span class="value">{{ result.embedding.length }}</span>
        </div>
      </div>

      <div class="embedding-preview">
        <h3>Embedding 前 10 位预览</h3>
        <pre>{{ previewEmbedding }}</pre>
      </div>

      <div class="embedding-preview">
        <h3>完整返回 JSON</h3>
        <pre>{{ result }}</pre>
      </div>
    </section>
  </div>
</template>

<style scoped>
.page {
  max-width: 1080px;
  margin: 0 auto;
  padding: 32px 24px;
  color: #172033;
}

.page-header {
  margin-bottom: 24px;
}

.eyebrow {
  margin: 0 0 8px;
  font-size: 13px;
  color: #2563eb;
  font-weight: 700;
}

h1 {
  margin: 0;
  font-size: 30px;
}

.desc {
  margin-top: 10px;
  color: #64748b;
  line-height: 1.7;
}

.card {
  background: #ffffff;
  border: 1px solid #e5e7eb;
  border-radius: 16px;
  padding: 20px;
  box-shadow: 0 8px 24px rgba(15, 23, 42, 0.06);
  margin-bottom: 18px;
}

.label {
  display: block;
  font-weight: 700;
  margin-bottom: 10px;
}

.input-row {
  display: flex;
  gap: 12px;
  align-items: center;
}

.input {
  flex: 1;
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 0 12px;
  font-size: 14px;
}

.btn {
  height: 40px;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  background: #ffffff;
  padding: 0 16px;
  cursor: pointer;
  font-weight: 600;
}

.btn.primary {
  background: #2563eb;
  color: #ffffff;
  border-color: #2563eb;
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.tip {
  margin: 12px 0 0;
  color: #64748b;
  font-size: 13px;
}

.error-card {
  border: 1px solid #fecaca;
  background: #fef2f2;
  color: #b91c1c;
  border-radius: 14px;
  padding: 14px 16px;
  margin-bottom: 18px;
}

.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.result-header h2 {
  margin: 0;
}

.status {
  background: #dcfce7;
  color: #166534;
  border-radius: 999px;
  padding: 4px 10px;
  font-size: 12px;
  font-weight: 700;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 14px;
  margin-top: 18px;
}

.item {
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  padding: 12px;
  background: #f8fafc;
}

.key {
  display: block;
  font-size: 12px;
  color: #64748b;
  margin-bottom: 6px;
}

.value {
  font-weight: 700;
  word-break: break-all;
}

.embedding-preview {
  margin-top: 20px;
}

.embedding-preview h3 {
  margin-bottom: 10px;
  font-size: 16px;
}

pre {
  background: #0f172a;
  color: #e5e7eb;
  border-radius: 12px;
  padding: 14px;
  overflow: auto;
  line-height: 1.6;
  font-size: 13px;
}
.section-title {
  margin-bottom: 16px;
}

.checkbox {
  display: flex;
  align-items: center;
  gap: 6px;
  white-space: nowrap;
  color: #334155;
  font-size: 14px;
}

.table {
  width: 100%;
  border-collapse: collapse;
  background: #ffffff;
  font-size: 14px;
}

.table th,
.table td {
  border: 1px solid #e5e7eb;
  padding: 10px;
  text-align: left;
}

.table th {
  background: #f8fafc;
  color: #334155;
  font-weight: 700;
}

.table td {
  color: #475569;
}
.textarea {
  width: 100%;
  border: 1px solid #d1d5db;
  border-radius: 10px;
  padding: 12px;
  font-size: 14px;
  line-height: 1.7;
  resize: vertical;
  box-sizing: border-box;
  margin-bottom: 14px;
}

.search-row {
  align-items: flex-end;
}

.field {
  min-width: 160px;
}
</style>