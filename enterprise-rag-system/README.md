# 企业内部知识库智能问答系统

> 基于 RAG（Retrieval-Augmented Generation）的企业级知识库问答平台，支持 PDF / Word / Excel 多格式文档接入，混合检索 + Rerank 精排，Q&A 准确率达 91%。

---

## ✨ 功能特性

- **多格式文档解析**：PDF（含扫描件 OCR）、Word、Excel、TXT、Markdown
- **三层分块策略**：规则分块 → 语义分块 → ParentDocumentRetriever 父子检索
- **BGE-M3 双向量**：Dense + Sparse 混合，RRF 融合排序，无需标注数据
- **BGE-Reranker-v2-m3**：CrossEncoder 精排，Top-20 → Top-5，大幅提升准确率
- **流式输出**：FastAPI SSE 实时流式回答，打字机效果
- **对话历史**：Redis 持久化，多轮对话上下文感知
- **Vue 3 前端**：实时对话界面、文档管理、语义检索调试面板
- **JWT 认证**：Token 鉴权，角色权限控制（管理员/普通用户）
- **Docker 一键部署**：Milvus + Redis + FastAPI + Vue + Nginx 全栈容器化

---

## 🏗️ 系统架构

```
用户浏览器
    │
    ▼
 [Nginx]  ← 反向代理 + 静态资源
    │
    ├──► [Vue 3 前端]  — 对话界面 / 文档管理 / 语义检索
    │
    └──► [FastAPI 后端]
              │
    ┌─────────┴──────────────────────┐
    │                                │
[RAG Chain (LangChain LCEL)]   [文档管理 API]
    │                                │
    ├── 问题改写（历史感知）          ├── 文档解析（PDF/Word/Excel）
    ├── 混合检索（Milvus RRF）        ├── 三层分块
    ├── BGE-Reranker 精排             └── BGE-M3 向量化 → Milvus
    └── LLM 流式生成
              │
    [Redis 对话历史]    [Milvus 2.5 向量库]
```

---

## 📊 技术栈

| 层次 | 技术 |
|------|------|
| 前端 | Vue 3 + Vite + Pinia + TailwindCSS |
| 后端 | FastAPI + LangChain v0.2+ LCEL |
| Embedding | BAAI/bge-m3（1024 维，Dense + Sparse） |
| Reranker | BAAI/bge-reranker-v2-m3（CrossEncoder） |
| 向量数据库 | Milvus 2.5 Standalone（HNSW + SPARSE_INVERTED_INDEX） |
| 对话历史 | Redis 7 + RedisChatMessageHistory |
| 部署 | Docker Compose + Nginx |

---

## 🚀 快速开始

### 前置条件

- Docker & Docker Compose（推荐 Docker Desktop 4.x+）
- 16 GB+ 内存（Milvus + BGE-M3 + Reranker 合计约 8-10 GB）
- LLM API Key（支持 OpenAI / DeepSeek / 通义千问）

### 1. 克隆项目

```bash
git clone https://github.com/your-username/enterprise-rag-system.git
cd enterprise-rag-system
```

### 2. 配置环境变量

```bash
cp .env.example .env
# 编辑 .env，填写 LLM_API_KEY 等必填项
vim .env
```

**必须配置的字段：**

| 字段 | 说明 | 示例 |
|------|------|------|
| `LLM_API_KEY` | LLM 服务 API Key | `sk-xxx` |
| `LLM_MODEL` | 模型名称 | `gpt-4o` / `deepseek-chat` |
| `SECRET_KEY` | JWT 签名密钥 | `openssl rand -hex 32` 生成 |

### 3. 一键启动

```bash
docker compose up -d
```

> 首次启动会自动下载 Milvus、Redis 等镜像，BGE-M3 / Reranker 模型会在首次请求时自动下载到 `model_cache` 卷（约 2-3 GB，需等待）。

### 4. 访问

- **前端**：http://localhost
- **API 文档**：http://localhost/docs
- **健康检查**：http://localhost/health

默认账号：`admin / admin123`（普通用户：`user / user123`）

---

## 🛠️ 本地开发

### 后端

```bash
cd backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt

# 确保 Milvus 和 Redis 已启动（可单独用 docker compose 启动）
docker compose up -d milvus redis

# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev  # 访问 http://localhost:5173
```

---

## 📁 项目结构

```
enterprise-rag-system/
├── backend/
│   ├── app/
│   │   ├── api/
│   │   │   ├── auth.py          # 认证接口
│   │   │   ├── chat.py          # 问答接口（SSE 流式）
│   │   │   └── documents.py     # 文档管理接口
│   │   ├── core/
│   │   │   ├── config.py        # 全局配置（env 注入）
│   │   │   └── security.py      # JWT 工具
│   │   ├── services/
│   │   │   ├── rag_service.py   # RAG 核心逻辑
│   │   │   ├── milvus_service.py# Milvus 混合检索
│   │   │   └── doc_service.py   # 文档解析与入库
│   │   ├── schemas/
│   │   │   └── chat.py          # Pydantic 数据模型
│   │   ├── utils/
│   │   │   └── document_loader.py # 多格式文档解析
│   │   └── main.py              # FastAPI 入口
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── views/
│   │   │   ├── LoginView.vue    # 登录页
│   │   │   ├── LayoutView.vue   # 主布局（侧边栏）
│   │   │   ├── ChatView.vue     # 智能问答页
│   │   │   ├── DocumentsView.vue# 文档管理页
│   │   │   └── SearchView.vue   # 语义检索调试页
│   │   ├── stores/
│   │   │   ├── auth.js          # 认证状态
│   │   │   └── chat.js          # 会话状态
│   │   ├── api/http.js          # Axios 封装
│   │   └── router/index.js      # 路由配置
│   ├── package.json
│   └── Dockerfile
├── nginx/
│   └── nginx.conf               # Nginx 反向代理配置
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## ⚙️ 准确率优化路径

| 阶段 | 优化措施 | 准确率 |
|------|---------|--------|
| 基线 | 纯 Dense 检索（bge-large-zh） | 72% |
| 阶段1 | 升级 bge-m3 + HNSW 调优 | ~76% |
| 阶段2 | Sparse 检索 + RRF 融合 | ~81% |
| 阶段3 | BGE-Reranker-v2-m3 精排 | ~87% |
| 阶段4 | ParentDocumentRetriever + HyDE | ~90% |
| 阶段5 | Multi-Query 扩展 + Prompt 优化 | ~91% |

---

## 🔧 常见问题

**Q：首次启动模型下载很慢？**  
A：BGE-M3 约 2.3 GB，Reranker 约 1.1 GB，建议使用 HuggingFace 镜像加速：
```bash
# 在 .env 中添加
HF_ENDPOINT=https://hf-mirror.com
```

**Q：没有 GPU 能运行吗？**  
A：可以，将 `.env` 中 `EMBEDDING_DEVICE=cpu`、`RERANKER_DEVICE=cpu`（已默认）。纯 CPU 下单次检索约 3-8 秒，生产环境建议配备 GPU。

**Q：如何切换 LLM 为 DeepSeek？**  
A：修改 `.env`：
```
LLM_API_KEY=sk-your-deepseek-key
LLM_BASE_URL=https://api.deepseek.com/v1
LLM_MODEL=deepseek-chat
```

**Q：如何重置 Milvus 数据？**  
```bash
docker compose down -v   # 删除所有 volume，谨慎操作
docker compose up -d
```

---

## 📄 License

MIT License — 详见 [LICENSE](LICENSE)

---

## 🙏 致谢

- [BAAI/FlagEmbedding](https://github.com/FlagOpen/FlagEmbedding) — BGE-M3 & BGE-Reranker
- [LangChain](https://github.com/langchain-ai/langchain) — RAG 框架
- [Milvus](https://github.com/milvus-io/milvus) — 向量数据库
- [FastAPI](https://fastapi.tiangolo.com/) — 后端框架
- [Vue 3](https://vuejs.org/) — 前端框架
