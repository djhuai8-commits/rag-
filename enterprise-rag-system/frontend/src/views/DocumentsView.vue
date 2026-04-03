<template>
  <div class="flex flex-col h-full">
    <!-- 顶栏 -->
    <header class="flex items-center justify-between px-6 py-3 border-b bg-white shadow-sm">
      <h2 class="font-semibold text-gray-700">📁 文档管理</h2>
      <button
        @click="showUpload = true"
        class="bg-indigo-600 hover:bg-indigo-700 text-white text-sm rounded-lg px-4 py-2 transition"
      >
        + 上传文档
      </button>
    </header>

    <div class="flex-1 overflow-y-auto p-6">
      <!-- 统计卡片 -->
      <div class="grid grid-cols-3 gap-4 mb-6">
        <div class="bg-white rounded-xl border p-4 shadow-sm">
          <p class="text-2xl font-bold text-indigo-600">{{ stats.row_count ?? '—' }}</p>
          <p class="text-xs text-gray-500 mt-1">向量总数</p>
        </div>
        <div class="bg-white rounded-xl border p-4 shadow-sm">
          <p class="text-2xl font-bold text-green-600">{{ stats.ready_count ?? '—' }}</p>
          <p class="text-xs text-gray-500 mt-1">已就绪文档</p>
        </div>
        <div class="bg-white rounded-xl border p-4 shadow-sm">
          <p class="text-2xl font-bold text-yellow-500">{{ stats.processing_count ?? '—' }}</p>
          <p class="text-xs text-gray-500 mt-1">处理中</p>
        </div>
      </div>

      <!-- 文档列表 -->
      <div class="bg-white rounded-xl border shadow-sm overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 text-gray-600">
            <tr>
              <th class="text-left px-4 py-3 font-medium">文件名</th>
              <th class="text-left px-4 py-3 font-medium">类型</th>
              <th class="text-left px-4 py-3 font-medium">部门</th>
              <th class="text-left px-4 py-3 font-medium">Chunk 数</th>
              <th class="text-left px-4 py-3 font-medium">状态</th>
              <th v-if="auth.isAdmin" class="text-left px-4 py-3 font-medium">操作</th>
            </tr>
          </thead>
          <tbody>
            <tr v-if="docs.length === 0">
              <td colspan="6" class="text-center text-gray-400 py-12">
                暂无文档，请上传文档后使用
              </td>
            </tr>
            <tr
              v-for="doc in docs"
              :key="doc.id"
              class="border-t hover:bg-gray-50 transition"
            >
              <td class="px-4 py-3 font-medium text-gray-700 max-w-xs truncate">{{ doc.filename }}</td>
              <td class="px-4 py-3">
                <span class="bg-blue-50 text-blue-600 text-xs rounded px-2 py-0.5 uppercase">{{ doc.doc_type }}</span>
              </td>
              <td class="px-4 py-3 text-gray-600">{{ doc.department }}</td>
              <td class="px-4 py-3 text-gray-600">{{ doc.chunk_count }}</td>
              <td class="px-4 py-3">
                <span :class="statusClass(doc.status)">{{ statusLabel(doc.status) }}</span>
              </td>
              <td v-if="auth.isAdmin" class="px-4 py-3">
                <button
                  @click="deleteDoc(doc.id)"
                  class="text-red-400 hover:text-red-600 text-xs transition"
                >删除</button>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>

    <!-- 上传弹窗 -->
    <Teleport to="body">
      <div v-if="showUpload" class="fixed inset-0 bg-black/40 flex items-center justify-center z-50">
        <div class="bg-white rounded-2xl shadow-2xl p-8 w-full max-w-md">
          <h3 class="font-bold text-lg text-gray-800 mb-5">上传文档</h3>

          <!-- 拖拽区域 -->
          <div
            @dragover.prevent
            @drop.prevent="handleDrop"
            @click="fileInput.click()"
            class="border-2 border-dashed border-indigo-300 rounded-xl p-8 text-center cursor-pointer hover:border-indigo-500 hover:bg-indigo-50 transition mb-4"
          >
            <p class="text-2xl mb-2">📄</p>
            <p class="text-gray-600 text-sm">点击或拖拽文件到此处</p>
            <p class="text-gray-400 text-xs mt-1">支持 PDF、Word、Excel、TXT、Markdown，最大 50 MB</p>
            <input ref="fileInput" type="file" class="hidden" multiple :accept="acceptTypes" @change="handleFileSelect" />
          </div>

          <!-- 已选文件列表 -->
          <div v-if="selectedFiles.length" class="mb-4 space-y-2">
            <div v-for="f in selectedFiles" :key="f.name" class="flex items-center justify-between bg-gray-50 rounded-lg px-3 py-2 text-sm">
              <span class="truncate text-gray-700">{{ f.name }}</span>
              <span class="text-gray-400 ml-2 shrink-0">{{ formatSize(f.size) }}</span>
            </div>
          </div>

          <!-- 部门选择 -->
          <div class="mb-5">
            <label class="block text-sm font-medium text-gray-700 mb-1">所属部门</label>
            <select v-model="uploadDept" class="w-full border rounded-lg px-3 py-2 text-sm focus:ring-2 focus:ring-indigo-300">
              <option value="general">通用</option>
              <option value="hr">人力资源</option>
              <option value="finance">财务</option>
              <option value="tech">技术</option>
              <option value="product">产品</option>
              <option value="legal">法务</option>
            </select>
          </div>

          <p v-if="uploadError" class="text-red-500 text-sm mb-3">{{ uploadError }}</p>

          <div class="flex gap-3">
            <button @click="showUpload = false; selectedFiles = []" class="flex-1 border rounded-lg py-2.5 text-sm text-gray-600 hover:bg-gray-50 transition">取消</button>
            <button
              @click="doUpload"
              :disabled="!selectedFiles.length || uploading"
              class="flex-1 bg-indigo-600 hover:bg-indigo-700 disabled:bg-indigo-300 text-white rounded-lg py-2.5 text-sm font-medium transition"
            >
              {{ uploading ? '上传中…' : '确认上传' }}
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import api from '@/api/http'
import { useAuthStore } from '@/stores/auth'

const auth = useAuthStore()
const docs = ref([])
const stats = ref({})
const showUpload  = ref(false)
const selectedFiles = ref([])
const uploadDept  = ref('general')
const uploading   = ref(false)
const uploadError = ref('')
const fileInput   = ref(null)
const acceptTypes = '.pdf,.docx,.doc,.xlsx,.xls,.txt,.md'

let pollTimer = null

async function fetchDocs() {
  const [docRes, statRes] = await Promise.all([
    api.get('/api/documents'),
    api.get('/api/documents/stats'),
  ])
  docs.value  = docRes.data.documents
  stats.value = statRes.data
}

onMounted(() => {
  fetchDocs()
  pollTimer = setInterval(fetchDocs, 5000)  // 每5秒轮询状态
})
onUnmounted(() => clearInterval(pollTimer))

function handleDrop(e) {
  selectedFiles.value = [...e.dataTransfer.files]
}
function handleFileSelect(e) {
  selectedFiles.value = [...e.target.files]
}

async function doUpload() {
  uploading.value = true
  uploadError.value = ''
  try {
    for (const file of selectedFiles.value) {
      const form = new FormData()
      form.append('file', file)
      form.append('department', uploadDept.value)
      await api.post('/api/documents/upload', form)
    }
    showUpload.value = false
    selectedFiles.value = []
    await fetchDocs()
  } catch (e) {
    uploadError.value = e.response?.data?.detail || '上传失败'
  } finally {
    uploading.value = false
  }
}

async function deleteDoc(id) {
  if (!confirm('确定删除该文档及其所有向量数据？')) return
  await api.delete(`/api/documents/${id}`)
  await fetchDocs()
}

function statusLabel(s) {
  return { ready: '✅ 就绪', processing: '⏳ 处理中', failed: '❌ 失败' }[s] ?? s
}
function statusClass(s) {
  return {
    ready:      'text-green-600 text-xs',
    processing: 'text-yellow-500 text-xs',
    failed:     'text-red-500 text-xs',
  }[s] ?? 'text-gray-500 text-xs'
}
function formatSize(bytes) {
  if (bytes < 1024) return bytes + ' B'
  if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
  return (bytes / 1024 / 1024).toFixed(1) + ' MB'
}
</script>
