<template>
  <div class="flex h-screen overflow-hidden">
    <!-- 侧边栏 -->
    <aside class="w-56 bg-gray-900 text-white flex flex-col shrink-0">
      <div class="px-5 py-5 border-b border-gray-700">
        <div class="flex items-center gap-2">
          <span class="text-2xl">🧠</span>
          <div>
            <p class="font-bold text-sm leading-tight">企业知识库</p>
            <p class="text-gray-400 text-xs">智能问答系统</p>
          </div>
        </div>
      </div>

      <nav class="flex-1 p-3 space-y-1">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition hover:bg-gray-700"
          active-class="bg-indigo-600 text-white"
          inactive-class="text-gray-300"
        >
          <span>{{ item.icon }}</span>
          <span>{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="p-4 border-t border-gray-700">
        <div class="flex items-center gap-2 text-sm text-gray-300 mb-3">
          <span>👤</span>
          <span>{{ auth.username }}</span>
          <span v-if="auth.isAdmin" class="text-xs bg-indigo-500 text-white px-1.5 rounded">管理员</span>
        </div>
        <button
          @click="handleLogout"
          class="w-full text-sm text-gray-400 hover:text-white bg-gray-800 hover:bg-gray-700 rounded-lg py-2 transition"
        >
          退出登录
        </button>
      </div>
    </aside>

    <!-- 主内容 -->
    <main class="flex-1 overflow-hidden">
      <router-view />
    </main>
  </div>
</template>

<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'

const auth   = useAuthStore()
const router = useRouter()

const navItems = [
  { path: '/chat',   icon: '💬', label: '智能问答' },
  { path: '/docs',   icon: '📁', label: '文档管理' },
  { path: '/search', icon: '🔍', label: '语义检索' },
]

function handleLogout() {
  auth.logout()
  router.push('/login')
}
</script>
