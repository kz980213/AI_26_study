<template>
  <div class="min-h-screen bg-gray-50">
    <!-- 顶部导航 -->
    <header class="bg-white shadow-sm border-b">
      <div class="max-w-6xl mx-auto px-4 py-3 flex items-center justify-between">
        <h1 class="text-xl font-bold text-gray-800">Enterprise Knowledge Base</h1>
        <div v-if="auth.isLoggedIn" class="flex items-center gap-4">
          <span class="text-sm text-gray-500">{{ auth.username }}</span>
          <button
            @click="auth.logout()"
            class="text-sm text-red-600 hover:text-red-800 cursor-pointer"
          >
            退出登录
          </button>
        </div>
      </div>
    </header>

    <!-- 登录/注册 -->
    <div v-if="!auth.isLoggedIn" class="max-w-md mx-auto mt-20 px-4">
      <div class="bg-white rounded-lg shadow p-6">
        <h2 class="text-lg font-semibold mb-4">
          {{ isRegister ? '注册账号' : '登录' }}
        </h2>

        <div v-if="errorMsg" class="mb-3 p-2 bg-red-50 text-red-600 text-sm rounded">
          {{ errorMsg }}
        </div>

        <input
          v-model="formUser"
          type="text"
          placeholder="用户名"
          class="w-full mb-3 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
          @keyup.enter="handleSubmit"
        />
        <input
          v-model="formPass"
          type="password"
          placeholder="密码"
          class="w-full mb-4 px-3 py-2 border rounded focus:outline-none focus:ring-2 focus:ring-blue-400"
          @keyup.enter="handleSubmit"
        />
        <button
          @click="handleSubmit"
          class="w-full py-2 bg-blue-600 text-white rounded hover:bg-blue-700 cursor-pointer"
        >
          {{ isRegister ? '注册' : '登录' }}
        </button>
        <p class="mt-3 text-sm text-center text-gray-500">
          <span @click="isRegister = !isRegister" class="text-blue-600 cursor-pointer hover:underline">
            {{ isRegister ? '已有账号？去登录' : '没有账号？去注册' }}
          </span>
        </p>
      </div>
    </div>

    <!-- 主界面 -->
    <div v-else class="max-w-6xl mx-auto px-4 py-6 flex gap-6">
      <!-- 左侧：召回参数面板 -->
      <aside class="w-64 flex-shrink-0">
        <RecallPanel
          :topK="recallTopK"
          :threshold="recallThreshold"
          :fileFilter="recallFileFilter"
          @update:topK="recallTopK = $event"
          @update:threshold="recallThreshold = $event"
          @update:fileFilter="recallFileFilter = $event"
        />
      </aside>

      <!-- 右侧：对话区 -->
      <main class="flex-1">
        <ChatPanel
          :token="auth.token || ''"
          :topK="recallTopK"
          :threshold="recallThreshold"
          :fileFilter="recallFileFilter"
        />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useAuthStore } from './stores/auth'
import ChatPanel from './components/ChatPanel.vue'
import RecallPanel from './components/RecallPanel.vue'

const auth = useAuthStore()
const isRegister = ref(false)
const formUser = ref('')
const formPass = ref('')
const errorMsg = ref('')

const recallTopK = ref(5)
const recallThreshold = ref(0.3)
const recallFileFilter = ref('')

async function handleSubmit() {
  errorMsg.value = ''
  try {
    if (isRegister.value) {
      await auth.register(formUser.value, formPass.value)
      isRegister.value = false
      errorMsg.value = '注册成功，请登录'
    } else {
      await auth.login(formUser.value, formPass.value)
    }
  } catch (e) {
    errorMsg.value = (e as Error).message
  }
}
</script>
