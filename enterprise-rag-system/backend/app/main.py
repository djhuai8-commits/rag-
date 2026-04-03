"""
FastAPI 应用入口
"""
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

from app.core.config import settings
from app.api import auth, chat, documents

# ── 日志配置 ────────────────────────────────────────
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)


# ── 生命周期 ─────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info(f"启动 {settings.APP_NAME} v{settings.APP_VERSION}")
    # 预热 RAG 服务（加载 Embedding / Reranker 模型）
    try:
        from app.services.rag_service import get_rag_service
        get_rag_service()
        logger.info("RAG 服务初始化完成")
    except Exception as e:
        logger.warning(f"RAG 服务初始化失败（可能缺少模型或 Milvus 未启动）：{e}")
    yield
    logger.info("服务关闭")


# ── 速率限制 ─────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=[settings.RATE_LIMIT])


# ── FastAPI 实例 ──────────────────────────────────────
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="基于 RAG 的企业内部知识库智能问答系统",
    lifespan=lifespan,
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── CORS ─────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],      # 生产环境替换为具体域名
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 路由注册 ─────────────────────────────────────────
app.include_router(auth.router)
app.include_router(chat.router)
app.include_router(documents.router)


# ── 健康检查 ─────────────────────────────────────────
@app.get("/health", tags=["系统"])
async def health_check():
    from app.services.milvus_service import get_milvus_service
    import redis

    milvus_status = "ok"
    redis_status = "ok"

    try:
        get_milvus_service().get_collection_stats()
    except Exception:
        milvus_status = "error"

    try:
        r = redis.from_url(settings.REDIS_URL)
        r.ping()
    except Exception:
        redis_status = "error"

    return {
        "status": "ok",
        "milvus": milvus_status,
        "redis": redis_status,
        "version": settings.APP_VERSION,
    }


@app.get("/", tags=["系统"])
async def root():
    return {"message": f"欢迎使用 {settings.APP_NAME}", "docs": "/docs"}
