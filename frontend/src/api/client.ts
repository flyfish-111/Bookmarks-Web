import axios from 'axios'
import { ElMessage } from 'element-plus'

export const TOKEN_KEY = 'bookmarks_token'

export const http = axios.create({
  baseURL: '/api',
  timeout: 90000,
})

http.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const status = error?.response?.status
    const detail = error?.response?.data?.detail
    const msg = typeof detail === 'string' && detail ? detail : error?.message || '请求失败'
    const url: string = error?.config?.url || ''
    const isAuthRequest = url.includes('/auth/login') || url.includes('/auth/register')
    // 未登录/凭证失效：清 token 并跳登录页（登录/注册接口自身的 401 不跳转）
    if (status === 401 && !isAuthRequest) {
      localStorage.removeItem(TOKEN_KEY)
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    }
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)
