import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

const AUTH_KEY = 'kb_token'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(AUTH_KEY))
  const username = ref<string | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  async function login(user: string, password: string): Promise<void> {
    const resp = await fetch('/api/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password }),
    })

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error((err as Record<string, string>).detail || '登录失败')
    }

    const data = await resp.json()
    token.value = data.access_token
    username.value = user
    localStorage.setItem(AUTH_KEY, data.access_token)
  }

  async function register(user: string, password: string): Promise<void> {
    const resp = await fetch('/api/auth/register', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username: user, password }),
    })

    if (!resp.ok) {
      const err = await resp.json().catch(() => ({}))
      throw new Error((err as Record<string, string>).detail || '注册失败')
    }
  }

  function logout(): void {
    token.value = null
    username.value = null
    localStorage.removeItem(AUTH_KEY)
  }

  return { token, username, isLoggedIn, login, register, logout }
})
