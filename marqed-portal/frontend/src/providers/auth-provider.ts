import { AuthProvider } from '@refinedev/core'
import { axiosInstance } from './axios'

interface LoginResponse {
  access_token: string
  refresh_token: string
  token_type: string
  user: {
    id: string
    email: string
    full_name: string
    role: string
    tenant_id: string
  }
}

const TOKEN_KEY = 'marqed_access_token'
const REFRESH_TOKEN_KEY = 'marqed_refresh_token'
const USER_KEY = 'marqed_user'

export const authProvider: AuthProvider = {
  login: async ({ email, password }) => {
    try {
      const response = await axiosInstance.post<LoginResponse>('/api/auth/login', {
        email,
        password,
      })

      const { access_token, refresh_token, user } = response.data

      localStorage.setItem(TOKEN_KEY, access_token)
      localStorage.setItem(REFRESH_TOKEN_KEY, refresh_token)
      localStorage.setItem(USER_KEY, JSON.stringify(user))

      return {
        success: true,
        redirectTo: '/',
      }
    } catch (error) {
      return {
        success: false,
        error: {
          name: 'LoginError',
          message: 'Ongeldige inloggegevens',
        },
      }
    }
  },

  logout: async () => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(REFRESH_TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    return {
      success: true,
      redirectTo: '/login',
    }
  },

  check: async () => {
    const token = localStorage.getItem(TOKEN_KEY)
    if (!token) {
      return {
        authenticated: false,
        redirectTo: '/login',
        logout: true,
      }
    }

    try {
      await axiosInstance.get('/api/auth/me')
      return { authenticated: true }
    } catch {
      // Try to refresh token
      const refreshToken = localStorage.getItem(REFRESH_TOKEN_KEY)
      if (refreshToken) {
        try {
          const response = await axiosInstance.post<LoginResponse>(
            '/api/auth/refresh',
            { refresh_token: refreshToken }
          )
          localStorage.setItem(TOKEN_KEY, response.data.access_token)
          return { authenticated: true }
        } catch {
          // Refresh failed, logout
        }
      }
      return {
        authenticated: false,
        redirectTo: '/login',
        logout: true,
      }
    }
  },

  getPermissions: async () => {
    const userStr = localStorage.getItem(USER_KEY)
    if (userStr) {
      const user = JSON.parse(userStr)
      return user.role
    }
    return null
  },

  getIdentity: async () => {
    const userStr = localStorage.getItem(USER_KEY)
    if (userStr) {
      return JSON.parse(userStr)
    }
    return null
  },

  onError: async (error) => {
    if (error?.statusCode === 401) {
      return {
        redirectTo: '/login',
        logout: true,
        error,
      }
    }
    return { error }
  },
}

// Helper to get current access token
export const getAccessToken = (): string | null => {
  return localStorage.getItem(TOKEN_KEY)
}

// Helper to get current user
export const getCurrentUser = () => {
  const userStr = localStorage.getItem(USER_KEY)
  return userStr ? JSON.parse(userStr) : null
}
