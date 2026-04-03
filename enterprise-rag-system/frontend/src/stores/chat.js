import { defineStore } from 'pinia'
import { ref } from 'vue'
import api from '@/api/http'

export const useChatStore = defineStore('chat', () => {
  const sessions  = ref({})    // sessionId -> [{ role, content, id, sources }]
  const sessionId = ref('default')

  function currentMessages() {
    return sessions.value[sessionId.value] || []
  }

  function newSession() {
    sessionId.value = `session_${Date.now()}`
    sessions.value[sessionId.value] = []
  }

  function addMessage(role, content, sources = []) {
    if (!sessions.value[sessionId.value]) {
      sessions.value[sessionId.value] = []
    }
    const msg = { id: Date.now(), role, content, sources, ts: new Date() }
    sessions.value[sessionId.value].push(msg)
    return msg
  }

  function updateLastAssistant(content) {
    const msgs = sessions.value[sessionId.value]
    if (!msgs) return
    for (let i = msgs.length - 1; i >= 0; i--) {
      if (msgs[i].role === 'assistant') {
        msgs[i].content = content
        return
      }
    }
  }

  async function clearSession() {
    await api.delete(`/api/chat/history/${sessionId.value}`)
    sessions.value[sessionId.value] = []
  }

  return {
    sessions, sessionId,
    currentMessages, newSession, addMessage, updateLastAssistant, clearSession,
  }
})
