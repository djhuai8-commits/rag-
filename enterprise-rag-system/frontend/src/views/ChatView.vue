<template>
  <div class="flex flex-col h-full bg-white">
    <!-- 顶栏 -->
    <header class="flex items-center justify-between px-6 py-3 border-b bg-white shadow-sm">
      <h2 class="font-semibold text-gray-700">💬 智能问答</h2>
      <div class="flex gap-2">
        <button
          @click="chatStore.newSession()"
          class="text-sm text-gray-500 hover:text-indigo-600 border rounded-lg px-3 py-1.5 transition hover:border-indigo-300"
        >
          + 新对话
        </button>
        <button
          @click="handleClearSession"
          class="text-sm text-gray-400 hover:text-red-500 transition"
          title="清空当前会话"
        >
          🗑 清空
        </button>
      </div>
    </header>

    <!-- 消息列表 -->
    <div ref="messagesEl" class="flex-1 overflow-y-auto px-6 py-4 space-y-4">
      <!-- 欢迎提示 -->
      <div v-if="messages.length === 0" class="text-center text-gray-400 mt-16">
        <div class="text-5xl mb-4">🤖</div>
        <p class="text-lg font-medium">你好！我是企业知识库助手</p>
        <p class="text-sm mt-2">请输入你的问题，我会从文档库中为你找到答案</p>
        <div class="flex flex-wrap justify-center gap-2 mt-6">
          <button
            v-for="tip in suggestTips"
            :key="tip"
            @click="inputText = tip"
            class="text-sm bg-indigo-50 text-indigo-600 hover:bg-indigo-100 rounded-full px-4 py-1.5 transition"
          >
            {{ tip }}
          </button>
        </div>
      </div>

      <!-- 消息气泡 -->
      <div
        v-for="msg in messages"
        :key="msg.id"
        :class="['flex gap-3', msg.role === 'user' ? 'justify-end' : 'justify-start']"
      >
        <div v-if="msg.role === 'assistant'" class="shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm">🤖</div>
        <div :class="['max-w-[75%] rounded-2xl px-4 py-3 shadow-sm',
          msg.role === 'user'
            ? 'bg-indigo-600 text-white rounded-br-none'
            : 'bg-gray-50 text-gray-800 rounded-bl-none border']">
          <div v-if="msg.role === 'user'" class="text-sm whitespace-pre-wrap">{{ msg.content }}</div>
          <div v-else class="markdown-body text-sm" v-html="renderMd(msg.content)" />
          <!-- 来源标签 -->
          <div v-if="msg.sources?.length" class="mt-2 flex flex-wrap gap-1">
            <span class="text-xs text-gray-400">来源：</span>
            <span
              v-for="src in msg.sources"
              :key="src"
              class="text-xs bg-white text-indigo-500 border border-indigo-200 rounded px-2 py-0.5"
            >{{ src }}</span>
          </div>
        </div>
        <div v-if="msg.role === 'user'" class="shrink-0 w-8 h-8 rounded-full bg-indigo-600 flex items-center justify-center text-sm">👤</div>
      </div>

      <!-- 流式输出气泡 -->
      <div v-if="isStreaming" class="flex gap-3 justify-start">
        <div class="shrink-0 w-8 h-8 rounded-full bg-indigo-100 flex items-center justify-center text-sm">🤖</div>
        <div class="max-w-[75%] bg-gray-50 border rounded-2xl rounded-bl-none px-4 py-3 shadow-sm">
          <div class="markdown-body text-sm" v-html="renderMd(streamContent)" />
          <span v-if="streamContent" class="cursor text-indigo-400">▋</span>
          <div v-else class="flex gap-1 items-center h-5">
            <span class="w-2 h-2 bg-indigo-300 rounded-full animate-bounce" style="animation-delay:0ms" />
            <span class="w-2 h-2 bg-indigo-300 rounded-full animate-bounce" style="animation-delay:150ms" />
            <span class="w-2 h-2 bg-indigo-300 rounded-full animate-bounce" style="animation-delay:300ms" />
          </div>
        </div>
      </div>
    </div>

    <!-- 输入框 -->
    <div class="px-6 py-4 border-t bg-white">
      <div class="flex gap-3 items-end">
        <textarea
          v-model="inputText"
          @keydown.enter.exact.prevent="sendMessage"
          @keydown.shift.enter.exact="inputText += '\n'"
          placeholder="输入问题，Enter 发送，Shift+Enter 换行"
          :disabled="isStreaming"
          rows="1"
          class="flex-1 border border-gray-300 rounded-xl px-4 py-3 text-sm resize-none focus:outline-none focus:ring-2 focus:ring-indigo-400 transition disabled:bg-gray-50"
          style="max-height: 120px; overflow-y: auto"
        />
        <button
          @click="sendMessage"
          :disabled="isStreaming || !inputText.trim()"
          class="bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-xl px-5 py-3 text-sm font-medium transition shrink-0"
        >
          {{ isStreaming ? '…' : '发送' }}
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, nextTick } from 'vue'
import { marked } from 'marked'
import hljs from 'highlight.js'
import DOMPurify from 'dompurify'
import { useAuthStore } from '@/stores/auth'
import { useChatStore } from '@/stores/chat'

// Marked 配置
marked.setOptions({
  highlight: (code, lang) => {
    if (lang && hljs.getLanguage(lang)) return hljs.highlight(code, { language: lang }).value
    return hljs.highlightAuto(code).value
  },
  breaks: true,
})

const renderMd = (text) => DOMPurify.sanitize(marked.parse(text || ''))

const auth        = useAuthStore()
const chatStore   = useChatStore()
const messages    = computed(() => chatStore.currentMessages())
const inputText   = ref('')
const isStreaming = ref(false)
const streamContent = ref('')
const messagesEl  = ref(null)

const suggestTips = [
  '员工年假政策是什么？',
  '报销流程怎么操作？',
  '如何申请居家办公？',
  '公司培训制度有哪些？',
]

const scrollToBottom = async () => {
  await nextTick()
  if (messagesEl.value) {
    messagesEl.value.scrollTo({ top: messagesEl.value.scrollHeight, behavior: 'smooth' })
  }
}

async function sendMessage() {
  const question = inputText.value.trim()
  if (!question || isStreaming.value) return

  inputText.value = ''
  chatStore.addMessage('user', question)
  isStreaming.value  = true
  streamContent.value = ''
  await scrollToBottom()

  try {
    const res = await fetch('/api/chat/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${auth.token}`,
      },
      body: JSON.stringify({ question, session_id: chatStore.sessionId }),
    })

    if (!res.ok) throw new Error(`HTTP ${res.status}`)

    const reader  = res.body.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      const text = decoder.decode(value, { stream: true })
      for (const line of text.split('\n')) {
        if (!line.startsWith('data: ')) continue
        try {
          const data = JSON.parse(line.slice(6))
          if (data.type === 'token') {
            streamContent.value += data.content
            await scrollToBottom()
          } else if (data.type === 'done') {
            chatStore.addMessage('assistant', streamContent.value)
            streamContent.value = ''
            isStreaming.value = false
          } else if (data.type === 'error') {
            chatStore.addMessage('assistant', `⚠️ 出现错误：${data.message}`)
            isStreaming.value = false
          }
        } catch {}
      }
    }
  } catch (e) {
    chatStore.addMessage('assistant', `⚠️ 请求失败：${e.message}`)
    isStreaming.value = false
  }
  await scrollToBottom()
}

async function handleClearSession() {
  if (!confirm('确定清空当前会话历史？')) return
  await chatStore.clearSession()
}
</script>
