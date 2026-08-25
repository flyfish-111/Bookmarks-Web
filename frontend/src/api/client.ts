import axios from 'axios'
import { ElMessage } from 'element-plus'

export const http = axios.create({
  baseURL: '/api',
  timeout: 90000,
})

http.interceptors.response.use(
  (resp) => resp,
  (error) => {
    const detail = error?.response?.data?.detail
    const msg = typeof detail === 'string' && detail ? detail : error?.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  },
)
