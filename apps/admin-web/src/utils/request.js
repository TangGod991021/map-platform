import axios from 'axios'
import { ElMessage } from 'element-plus'

const service = axios.create({
  baseURL: '/prod-api',
  timeout: 20000
})

service.interceptors.request.use((config) => {
  const token = localStorage.getItem('map_platform_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

service.interceptors.response.use(
  (response) => {
    const body = response.data
    if (body && body.code === 200) {
      return body
    }
    const message = (body && body.msg) || '请求失败'
    ElMessage.error(message)
    if (body && body.code === 401) {
      localStorage.removeItem('map_platform_token')
      window.location.href = '/login'
    }
    return Promise.reject(new Error(message))
  },
  (error) => {
    const status = error.response?.status
    const message = error.response?.data?.msg || error.message || '网络错误'
    if (status === 401) {
      localStorage.removeItem('map_platform_token')
      if (window.location.pathname !== '/login') {
        window.location.href = '/login'
      }
    } else {
      ElMessage.error(message)
    }
    return Promise.reject(error)
  }
)

export default service
