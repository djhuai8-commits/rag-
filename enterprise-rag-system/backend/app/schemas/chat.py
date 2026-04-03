"""
Pydantic 数据模型
"""
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime


# ── 认证 ──────────────────────────────────────────────
class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LoginRequest(BaseModel):
    username: str
    password: str


# ── 对话 ──────────────────────────────────────────────
class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=2000, description="用户问题")
    session_id: str = Field(default="default", description="会话 ID，用于维护对话历史")
    department_filter: Optional[str] = Field(None, description="部门过滤（可选）")
    top_k: int = Field(default=5, ge=1, le=20, description="返回文档数量")


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatHistoryResponse(BaseModel):
    session_id: str
    messages: List[ChatMessage]


# ── 文档 ──────────────────────────────────────────────
class DocumentInfo(BaseModel):
    id: str
    filename: str
    doc_type: str
    department: str
    chunk_count: int
    created_at: datetime
    status: str  # "processing" | "ready" | "failed"


class DocumentListResponse(BaseModel):
    total: int
    documents: List[DocumentInfo]


class DeleteDocumentResponse(BaseModel):
    message: str
    deleted_chunks: int


# ── 检索结果 ──────────────────────────────────────────
class RetrievedChunk(BaseModel):
    content: str
    source: str
    score: float
    department: Optional[str] = None


class SearchResponse(BaseModel):
    query: str
    chunks: List[RetrievedChunk]


# ── 系统状态 ──────────────────────────────────────────
class HealthResponse(BaseModel):
    status: str
    milvus: str
    redis: str
    version: str
