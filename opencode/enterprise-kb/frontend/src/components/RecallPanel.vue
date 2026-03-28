<template>
  <div class="bg-white rounded-lg shadow p-4 space-y-5">
    <h3 class="text-sm font-semibold text-gray-700 border-b pb-2">召回参数</h3>

    <!-- Top K -->
    <div>
      <label class="block text-xs text-gray-500 mb-1">
        Top K: <span class="font-medium text-gray-700">{{ topK }}</span>
      </label>
      <input
        type="range"
        :min="1"
        :max="20"
        :value="topK"
        class="w-full accent-blue-600 cursor-pointer"
        @input="emit('update:topK', Number(($event.target as HTMLInputElement).value))"
      />
    </div>

    <!-- 相似度阈值 -->
    <div>
      <label class="block text-xs text-gray-500 mb-1">
        相似度阈值: <span class="font-medium text-gray-700">{{ threshold.toFixed(2) }}</span>
      </label>
      <input
        type="range"
        :min="0"
        :max="100"
        :value="Math.round(threshold * 100)"
        class="w-full accent-blue-600 cursor-pointer"
        @input="emit('update:threshold', Number(($event.target as HTMLInputElement).value) / 100)"
      />
    </div>

    <!-- 文件过滤 -->
    <div>
      <label class="block text-xs text-gray-500 mb-1">文件名过滤</label>
      <input
        type="text"
        :value="fileFilter"
        placeholder="输入文件名（可选）"
        class="w-full px-2 py-1.5 border rounded text-sm focus:outline-none focus:ring-2 focus:ring-blue-400"
        @input="emit('update:fileFilter', ($event.target as HTMLInputElement).value)"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  topK: number
  threshold: number
  fileFilter: string
}>()

const emit = defineEmits<{
  'update:topK': [value: number]
  'update:threshold': [value: number]
  'update:fileFilter': [value: string]
}>()
</script>
