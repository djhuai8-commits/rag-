"""
文档管理接口
POST   /api/documents/upload      — 上传文档（异步处理）
GET    /api/documents             — 文档列表
DELETE /api/documents/{doc_id}    — 删除文档
GET    /api/documents/stats       — 向量库统计
"""
import uuid
import logging
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks

from app.core.security import get_current_user
from app.core.config import settings
from app.services.doc_service import (
    save_upload_file,
    process_document_async,
    list_documents,
    delete_document,
)
from app.services.milvus_service import get_milvus_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/documents", tags=["文档管理"])


@router.post("/upload")
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    department: str = Form(default="general"),
    current_user: dict = Depends(get_current_user),
):
    """上传文档并触发后台异步处理"""
    # 校验文件大小
    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE_MB * 1024 * 1024:
        raise HTTPException(400, f"文件大小超过限制（最大 {settings.MAX_FILE_SIZE_MB} MB）")

    # 校验文件格式
    ext = file.filename.rsplit(".", 1)[-1].lower() if "." in file.filename else ""
    if ext not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(400, f"不支持的文件格式：.{ext}，支持：{settings.ALLOWED_EXTENSIONS}")

    # 保存到磁盘
    file_path = await save_upload_file(file.filename, content)
    doc_id = uuid.uuid4().hex

    # 后台异步处理
    background_tasks.add_task(
        process_document_async, doc_id, file_path, file.filename, department
    )

    return {
        "status": "accepted",
        "doc_id": doc_id,
        "filename": file.filename,
        "message": "文件已接收，正在后台处理，请稍后查询状态",
    }


@router.get("")
async def list_docs(current_user: dict = Depends(get_current_user)):
    """获取已上传文档列表"""
    docs = list_documents()
    return {"total": len(docs), "documents": docs}


@router.delete("/{doc_id}")
async def delete_doc(doc_id: str, current_user: dict = Depends(get_current_user)):
    """删除文档（同时清理向量库中的 chunk）"""
    if current_user.get("role") != "admin":
        raise HTTPException(403, "仅管理员可删除文档")
    deleted = delete_document(doc_id)
    return {"message": "删除成功", "deleted_chunks": deleted}


@router.get("/stats")
async def get_stats(current_user: dict = Depends(get_current_user)):
    """向量库统计信息"""
    milvus = get_milvus_service()
    stats = milvus.get_collection_stats()
    docs = list_documents()
    return {
        **stats,
        "doc_count": len(docs),
        "ready_count": sum(1 for d in docs if d["status"] == "ready"),
        "processing_count": sum(1 for d in docs if d["status"] == "processing"),
    }
