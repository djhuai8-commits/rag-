<template>
  <div class="flex flex-col h-full">
    <header class="px-6 py-3 border-b bg-white shadow-sm">
      <h2 class="font-semibold text-gray-700">🔍 语义检索调试</h2>
      <p class="text-xs text-gray-400 mt-0.5">直接查看检索到的文档片段，用于调试召回效果</p>
    </header>

    <div class="flex-1 overflow-y-auto p-6">
      <!-- 搜索框 -->
      <div class="flex gap-3 mb-6">
        <input
          v-model="query"
          @keydown.enter="doSearch"
          type="text"
          placeholder="输入检索词，按 Enter 搜索"
          class="flex-1 border rounded-xl px-4 py-3 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-400 transition"
        />
        <select v-model="topK" class="border rounded-xl px-3 py-3 text-sm text-gray-600">
          <option :value="3">Top 3</option>
          <option :value="5">Top 5</option>
          <option :value="10">Top 10</option>
        </select>
        <button
          @click="doSearch"
          :disabled="!query.trim() || loading"
          class="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-xl px-6 py-3 text-sm font-medium transition"
        >
          {{ loading ? '检索中…' : '检索' }}
        </button>
      </div>

      <!-- 结果 -->
      <div v-if="results.length" class="space-y-4">
        <div
          v-for="(item, idx) in results"
          :key="idx"
          class="bg-white border rounded-xl p-5 shadow-sm"
        >
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center gap-2">
              <span class="w-6 h-6 bg-indigo-600 text-white rounded-full flex items-center justify-center text-xs font-bold shrink-0">{{ idx + 1 }}</span>
              <span class="text-xs text-indigo-600 bg-indigo-50 rounded px-2 py-0.5">{{ item.source }}</span>
            </div>
            <span class="text-xs text-gray-400">相关度：{{ (item.score * 100).toFixed(1) }}%</span>
          </div>
          <p class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">{{ item.content }}</p>
        </div>
      </div>

      <div v-else-if="searched && !loading" class="text-center text-gray-400 mt-16">
        <p class="text-3xl mb-3">🔎</p>
        <p>未找到相关文档，请尝试其他关键词</p>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import api from '@/api/http'

const query   = ref('')
const topK    = ref(5)
const loading = ref(false)
const results = ref([])
const searched = ref(false)

async function doSearch() {
  if (!query.value.trim() || loading.value) return
  loading.value = true
  searched.value = true
  try {
    const res = await api.post(`/api/chat/search?query=${encodeURIComponent(query.value)}&top_k=${topK.value}`)
    results.value = res.data.results
  } catch (e) {
    results.value = []
  } finally {
    loading.value = false
  }
}
</script>
