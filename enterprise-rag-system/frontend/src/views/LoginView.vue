<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-indigo-50 to-blue-100">
    <div class="bg-white rounded-2xl shadow-xl p-10 w-full max-w-md">
      <!-- Logo -->
      <div class="text-center mb-8">
        <div class="text-5xl mb-3">🧠</div>
        <h1 class="text-2xl font-bold text-gray-800">企业知识库</h1>
        <p class="text-gray-500 text-sm mt-1">智能问答系统</p>
      </div>

      <form @submit.prevent="handleLogin" class="space-y-5">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">用户名</label>
          <input
            v-model="form.username"
            type="text"
            placeholder="请输入用户名"
            required
            class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
          />
        </div>
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">密码</label>
          <input
            v-model="form.password"
            type="password"
            placeholder="请输入密码"
            required
            class="w-full border border-gray-300 rounded-lg px-4 py-2.5 focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
          />
        </div>

        <p v-if="error" class="text-red-500 text-sm bg-red-50 rounded-lg px-3 py-2">{{ error }}</p>

        <button
          type="submit"
          :disabled="loading"
          class="w-full bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white font-semibold rounded-lg py-3 transition"
        >
          {{ loading ? '登录中…' : '登 录' }}
        </button>
      </form>

      <p class="text-center text-xs text-gray-400 mt-6">
        演示账号：admin / admin123 &nbsp;|&nbsp; user / user123
      </p>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router  = useRouter()
const route   = useRoute()
const auth    = useAuthStore()
const loading = ref(false)
const error   = ref('')
const form    = ref({ username: '', password: '' })

async function handleLogin() {
  loading.value = true
  error.value   = ''
  try {
    await auth.login(form.value.username, form.value.password)
    const redirect = route.query.redirect || '/chat'
    router.push(redirect)
  } catch (e) {
    error.value = e.response?.data?.detail || '登录失败，请检查用户名和密码'
  } finally {
    loading.value = false
  }
}
</script>
