<template>
  <div class="border rounded-lg bg-gray-50 p-3 text-sm">
    <div class="flex items-center gap-2 mb-1">
      <span class="inline-flex items-center justify-center w-5 h-5 rounded-full bg-blue-100 text-blue-700 text-xs font-semibold">
        {{ index }}
      </span>
      <span class="text-gray-500 text-xs">
        {{ citation.metadata?.file_name || '未知来源' }}
        <span v-if="citation.metadata?.page_num">, 第 {{ citation.metadata.page_num }} 页</span>
      </span>
      <span class="ml-auto text-xs text-gray-400">
        相关度: {{ (citation.score * 100).toFixed(0) }}%
      </span>
    </div>
    <p class="text-gray-700 leading-relaxed line-clamp-3">
      {{ citation.content }}
    </p>
  </div>
</template>

<script setup lang="ts">
import type { CitationItem } from '../api/chat'

defineProps<{
  citation: CitationItem
  index: number
}>()
</script>

<style scoped>
.line-clamp-3 {
  display: -webkit-box;
  -webkit-line-clamp: 3;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
</style>
