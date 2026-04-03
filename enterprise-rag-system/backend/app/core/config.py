"""
全局配置管理 — 通过环境变量注入，生产环境使用 .env 文件
"""
from pydantic_settings import BaseSettings
from functools import lru_cache


class Settings(BaseSettings):
    # ── 应用 ──────────────────────────────────────────
    APP_NAME: str = "企业知识库智能问答系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # ── JWT 认证 ──────────────────────────────────────
    SECRET_KEY: str = "change-me-in-production-use-openssl-rand-hex-32"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 8  # 8 小时

    # ── Milvus ────────────────────────────────────────
    MILVUS_URI: str = "http://localhost:19530"
    MILVUS_COLLECTION: str = "enterprise_kb"
    MILVUS_DIM: int = 1024  # BGE-M3 维度

    # ── Embedding 模型 ────────────────────────────────
    EMBEDDING_MODEL: str = "BAAI/bge-m3"
    EMBEDDING_DEVICE: str = "cpu"  # 有 GPU 改为 "cuda"
    EMBEDDING_BATCH_SIZE: int = 32

    # ── Reranker 模型 ─────────────────────────────────
    RERANKER_MODEL: str = "BAAI/bge-reranker-v2-m3"
    RERANKER_DEVICE: str = "cpu"
    RERANKER_TOP_N: int = 5

    # ── LLM ───────────────────────────────────────────
    LLM_PROVIDER: str = "openai"          # openai | deepseek | qwen
    LLM_API_KEY: str = ""
    LLM_BASE_URL: str = "https://api.openai.com/v1"
    LLM_MODEL: str = "gpt-4o"
    LLM_TEMPERATURE: float = 0.1
    LLM_MAX_TOKENS: int = 2048

    # ── Redis（对话历史）─────────────────────────────
    REDIS_URL: str = "redis://localhost:6379"

    # ── 文件上传 ──────────────────────────────────────
    UPLOAD_DIR: str = "/data/uploads"
    MAX_FILE_SIZE_MB: int = 50
    ALLOWED_EXTENSIONS: list[str] = ["pdf", "docx", "doc", "xlsx", "xls", "txt", "md"]

    # ── 检索参数 ──────────────────────────────────────
    RETRIEVAL_TOP_K: int = 20       # 混合检索返回数量
    RRF_K: int = 60                 # RRF 融合超参数
    CHUNK_SIZE: int = 512
    CHUNK_OVERLAP: int = 50
    PARENT_CHUNK_SIZE: int = 1024
    CHILD_CHUNK_SIZE: int = 200

    # ── 速率限制 ──────────────────────────────────────
    RATE_LIMIT: str = "20/minute"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
