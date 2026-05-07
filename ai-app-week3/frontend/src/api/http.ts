import axios from 'axios'
import { removeToken } from '../utils/storage'

const http = axios.create({
  baseURL: 'http://127.0.0.1:8010',
  timeout: 5000,
})

http.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
        config.headers['Authorization'] = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

http.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error?.response?.status === 401) {
      removeToken()
    }
    return Promise.reject(error)
  }
)

export default http