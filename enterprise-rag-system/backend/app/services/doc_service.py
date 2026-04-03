"""
文档管理服务 — 上传、异步处理、列表、删除
"""
from __future__ import annotations

import os
import uuid
import time
import asyncio
import aiofiles
import logging
from pathlib import Path
from typing import Dict, List

from app.core.config import settings
from app.utils.document_loader import load_document
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)

# 内存状态存储（生产环境替换为 Redis 或数据库）
_doc_registry: Dict[str, dict] = {}


def get_doc_registry() -> Dict[str, dict]:
    return _doc_registry


async def save_upload_file(filename: str, content: bytes) -> str:
    """保存上传文件到磁盘，返回文件路径"""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    safe_name = f"{uuid.uuid4().hex}_{filename}"
    file_path = str(upload_dir / safe_name)
    async with aiofiles.open(file_path, "wb") as f:
        await f.write(content)
    return file_path


async def process_document_async(
    doc_id: str,
    file_path: str,
    filename: str,
    department: str,
):
    """后台异步处理文档：解析 → 分块 → 向量化 → 入库"""
    _doc_registry[doc_id] = {
        "id": doc_id,
        "filename": filename,
        "doc_type": Path(filename).suffix.lstrip(".").lower(),
        "department": department,
        "status": "processing",
        "chunk_count": 0,
        "created_at": time.time(),
        "file_path": file_path,
    }
    try:
        loop = asyncio.get_event_loop()
        # 文档解析在线程池中执行（避免阻塞事件循环）
        docs = await loop.run_in_executor(None, load_document, file_path)
        rag = get_rag_service()
        chunk_count = await loop.run_in_executor(
            None, rag.process_and_index, docs, department
        )
        _doc_registry[doc_id].update({
            "status": "ready",
            "chunk_count": chunk_count,
        })
        logger.info(f"文档 {filename} 处理完成，写入 {chunk_count} 个 chunk")
    except Exception as e:
        _doc_registry[doc_id]["status"] = "failed"
        _doc_registry[doc_id]["error"] = str(e)
        logger.error(f"文档 {filename} 处理失败：{e}")


def list_documents() -> List[dict]:
    return list(_doc_registry.values())


def delete_document(doc_id: str) -> int:
    """从 Milvus 删除文档 chunk，返回删除数量"""
    doc = _doc_registry.get(doc_id)
    if not doc:
        return 0
    from app.services.milvus_service import get_milvus_service
    milvus = get_milvus_service()
    # 通过 source 字段删除（生产环境建议用 file_hash）
    deleted = milvus.delete_by_hash(doc.get("file_hash", ""))
    del _doc_registry[doc_id]
    # 删除磁盘文件
    try:
        os.remove(doc["file_path"])
    except Exception:
        pass
    return deleted
