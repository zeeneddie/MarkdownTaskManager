import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios'

export const axiosInstance = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor - add auth token
axiosInstance.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    const token = localStorage.getItem('marqed_access_token')
    if (token && config.headers) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Add tenant header if available
    const userStr = localStorage.getItem('marqed_user')
    if (userStr && config.headers) {
      const user = JSON.parse(userStr)
      if (user.tenant_id) {
        config.headers['X-Tenant-ID'] = user.tenant_id
      }
    }

    return config
  },
  (error) => Promise.reject(error)
)

// Response interceptor - handle errors
axiosInstance.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & {
      _retry?: boolean
    }

    // If 401 and not already retrying, try to refresh token
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      const refreshToken = localStorage.getItem('marqed_refresh_token')
      if (refreshToken) {
        try {
          const response = await axios.post('/api/auth/refresh', {
            refresh_token: refreshToken,
          })

          const { access_token } = response.data
          localStorage.setItem('marqed_access_token', access_token)

          if (originalRequest.headers) {
            originalRequest.headers.Authorization = `Bearer ${access_token}`
          }
          return axiosInstance(originalRequest)
        } catch (refreshError) {
          // Refresh failed, redirect to login
          localStorage.removeItem('marqed_access_token')
          localStorage.removeItem('marqed_refresh_token')
          localStorage.removeItem('marqed_user')
          window.location.href = '/login'
        }
      }
    }

    return Promise.reject(error)
  }
)
