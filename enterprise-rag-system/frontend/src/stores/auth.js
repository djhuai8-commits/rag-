import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import api from '@/api/http'

export const useAuthStore = defineStore('auth', () => {
  const token    = ref(localStorage.getItem('token') || '')
  const username = ref(localStorage.getItem('username') || '')
  const role     = ref(localStorage.getItem('role') || '')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin    = computed(() => role.value === 'admin')

  async function login(usernameVal, password) {
    const params = new URLSearchParams()
    params.append('username', usernameVal)
    params.append('password', password)
    const res = await api.post('/api/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    })
    token.value = res.data.access_token
    // 解析 JWT 获取用户信息
    const payload = JSON.parse(atob(res.data.access_token.split('.')[1]))
    username.value = payload.sub
    role.value     = payload.role || 'user'
    localStorage.setItem('token',    token.value)
    localStorage.setItem('username', username.value)
    localStorage.setItem('role',     role.value)
  }

  function logout() {
    token.value = username.value = role.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    localStorage.removeItem('role')
  }

  return { token, username, role, isLoggedIn, isAdmin, login, logout }
})
