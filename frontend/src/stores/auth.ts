import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { authApi } from '../api'
import { TOKEN_KEY } from '../api/client'
import type { User } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem(TOKEN_KEY))
  const user = ref<User | null>(null)

  const isAuthed = computed(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem(TOKEN_KEY, t)
  }

  async function register(username: string, password: string) {
    const res = await authApi.register(username, password)
    setToken(res.access_token)
    user.value = res.user
  }

  async function login(username: string, password: string) {
    const res = await authApi.login(username, password)
    setToken(res.access_token)
    user.value = res.user
  }

  async function fetchMe() {
    if (!token.value) return
    try {
      user.value = await authApi.me()
    } catch {
      logout()
    }
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
  }

  return { token, user, isAuthed, register, login, fetchMe, logout }
})
