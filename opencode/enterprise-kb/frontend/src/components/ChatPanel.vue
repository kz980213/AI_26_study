<template>
  <div class="flex flex-col h-[calc(100vh-120px)]">
    <!-- 消息列表 -->
    <div ref="msgContainer" class="flex-1 overflow-y-auto space-y-4 pb-4">
      <div v-if="messages.length === 0" class="flex items-center justify-center h-full text-gray-400">
        上传文档后开始提问
      </div>

      <div
        v-for="(msg, idx) in messages"
        :key="idx"
        :class="msg.role === 'user' ? 'flex justify-end' : 'flex justify-start'"
      >
        <div
          :class="[
            'max-w-[75%] rounded-lg px-4 py-2',
            msg.role === 'user'
              ? 'bg-blue-600 text-white'
              : 'bg-white shadow border',
          ]"
        >
          <div class="whitespace-pre-wrap text-sm" v-html="highlightCitations(msg.content)"></div>

          <!-- 引用卡片 -->
          <div v-if="msg.citations && msg.citations.length > 0" class="mt-2 space-y-2">
            <CitationCard
              v-for="(cite, ci) in msg.citations"
              :key="ci"
              :citation="cite"
              :index="ci + 1"
            />
          </div>
        </div>
      </div>

      <!-- 流式加载指示 -->
      <div v-if="isStreaming" class="flex justify-start">
        <div class="bg-white shadow border rounded-lg px-4 py-2">
          <span class="inline-flex gap-1">
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 0ms"></span>
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 150ms"></span>
            <span class="w-2 h-2 bg-gray-400 rounded-full animate-bounce" style="animation-delay: 300ms"></span>
          </span>
        </div>
      </div>
    </div>

    <!-- 输入区 -->
    <div class="border-t bg-white p-4">
      <div class="flex gap-3">
        <input
          v-model="inputText"
          type="text"
          placeholder="输入问题，按 Enter 发送..."
          class="flex-1 px-4 py-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-400"
          :disabled="isStreaming"
          @keyup.enter="sendMessage"
        />
        <button
          @click="sendMessage"
          :disabled="isStreaming || !inputText.trim()"
          class="px-6 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed cursor-pointer"
        >
          {{ isStreaming ? '生成中...' : '发送' }}
        </button>
      </div>

      <!-- 文件上传 -->
      <div class="mt-2">
        <input
          type="file"
          accept=".pdf,.md,.markdown"
          class="text-sm text-gray-500"
          @change="uploadFile"
        />
        <span v-if="uploadStatus" class="ml-2 text-sm" :class="uploadOk ? 'text-green-600' : 'text-red-600'">
          {{ uploadStatus }}
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, nextTick, watch } from 'vue'
import { streamChat, type CitationItem } from '../api/chat'
import CitationCard from './CitationCard.vue'

interface Message {
  role: 'user' | 'assistant'
  content: string
  citations: CitationItem[]
}

const props = defineProps<{
  token: string
  topK: number
  threshold: number
  fileFilter: string
}>()

const messages = ref<Message[]>([])
const inputText = ref('')
const isStreaming = ref(false)
const currentSessionId = ref<string | null>(null)
const uploadStatus = ref('')
const uploadOk = ref(false)
const msgContainer = ref<HTMLDivElement | null>(null)

function scrollToBottom() {
  nextTick(() => {
    if (msgContainer.value) {
      msgContainer.value.scrollTop = msgContainer.value.scrollHeight
    }
  })
}

watch(messages, scrollToBottom, { deep: true })

function highlightCitations(text: string): string {
  return text.replace(/\[(\d+)\]/g, '<sup class="text-blue-600 font-semibold">[$1]</sup>')
}

async function sendMessage() {
  const question = inputText.value.trim()
  if (!question || isStreaming.value) return

  messages.value.push({ role: 'user', content: question, citations: [] })
  messages.value.push({ role: 'assistant', content: '', citations: [] })
  inputText.value = ''
  isStreaming.value = true

  const assistantIdx = messages.value.length - 1

  await streamChat(
    question,
    props.token,
    currentSessionId.value,
    props.fileFilter || null,
    {
      onToken(content: string) {
        messages.value[assistantIdx].content += content
        scrollToBottom()
      },
      onDone(citations: CitationItem[]) {
        messages.value[assistantIdx].citations = citations
      },
      onError(msg: string) {
        messages.value[assistantIdx].content += `\n\n[错误] ${msg}`
      },
    },
  )

  isStreaming.value = false
  scrollToBottom()
}

async function uploadFile(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (!file) return

  uploadStatus.value = '上传中...'
  uploadOk.value = false

  const formData = new FormData()
  formData.append('file', file)

  try {
    const resp = await fetch(`/api/ingest/upload?token=${props.token}`, {
      method: 'POST',
      body: formData,
    })

    const data = await resp.json()
    if (resp.ok) {
      uploadStatus.value = data.message
      uploadOk.value = true
    } else {
      uploadStatus.value = data.detail || '上传失败'
      uploadOk.value = false
    }
  } catch (e) {
    uploadStatus.value = (e as Error).message
    uploadOk.value = false
  }

  target.value = ''
}
</script>
