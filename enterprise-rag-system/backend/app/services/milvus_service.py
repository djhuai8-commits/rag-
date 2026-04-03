"""
Milvus 向量库服务
- BGE-M3 Dense + Sparse 双向量存储
- HNSW 索引 + SPARSE_INVERTED_INDEX
- RRF 混合检索
"""
from __future__ import annotations

import time
import logging
from typing import List, Optional

from langchain.schema import Document
from langchain_community.embeddings import HuggingFaceBgeEmbeddings
from pymilvus import (
    MilvusClient,
    DataType,
    FieldSchema,
    CollectionSchema,
    AnnSearchRequest,
    RRFRanker,
)

from app.core.config import settings

logger = logging.getLogger(__name__)


class MilvusService:
    """封装 Milvus 向量库的所有操作"""

    def __init__(self):
        self.client = MilvusClient(uri=settings.MILVUS_URI)
        self.collection = settings.MILVUS_COLLECTION
        self.embeddings = HuggingFaceBgeEmbeddings(
            model_name=settings.EMBEDDING_MODEL,
            model_kwargs={"device": settings.EMBEDDING_DEVICE},
            encode_kwargs={
                "normalize_embeddings": True,
                "batch_size": settings.EMBEDDING_BATCH_SIZE,
            },
            query_instruction="为这个句子生成表示以用于检索相关文章：",
        )
        self._ensure_collection()

    # ── 集合管理 ──────────────────────────────────────

    def _ensure_collection(self):
        """如果集合不存在则创建"""
        if self.client.has_collection(self.collection):
            return
        fields = [
            FieldSchema("id",          DataType.INT64,              is_primary=True, auto_id=True),
            FieldSchema("text",        DataType.VARCHAR,             max_length=4096),
            FieldSchema("dense_vec",   DataType.FLOAT_VECTOR,        dim=settings.MILVUS_DIM),
            FieldSchema("sparse_vec",  DataType.SPARSE_FLOAT_VECTOR),
            FieldSchema("source",      DataType.VARCHAR,             max_length=512),
            FieldSchema("doc_type",    DataType.VARCHAR,             max_length=64),
            FieldSchema("department",  DataType.VARCHAR,             max_length=128),
            FieldSchema("file_hash",   DataType.VARCHAR,             max_length=64),
            FieldSchema("created_at",  DataType.INT64),
        ]
        schema = CollectionSchema(
            fields, description="Enterprise Knowledge Base", enable_dynamic_field=True
        )
        self.client.create_collection(self.collection, schema=schema)
        # Dense HNSW 索引
        self.client.create_index(
            self.collection, "dense_vec",
            {"index_type": "HNSW", "metric_type": "COSINE",
             "params": {"M": 16, "efConstruction": 200}},
        )
        # Sparse 倒排索引
        self.client.create_index(
            self.collection, "sparse_vec",
            {"index_type": "SPARSE_INVERTED_INDEX", "metric_type": "IP"},
        )
        self.client.load_collection(self.collection)
        logger.info(f"集合 '{self.collection}' 创建完成")

    def hash_exists(self, file_hash: str) -> bool:
        """检查文件是否已入库（通过 MD5）"""
        res = self.client.query(
            self.collection,
            filter=f'file_hash == "{file_hash}"',
            output_fields=["id"],
            limit=1,
        )
        return len(res) > 0

    # ── 写入 ──────────────────────────────────────────

    def add_documents(self, docs: List[Document], department: str = "general") -> int:
        """批量向量化并写入 Milvus，返回写入条数"""
        texts = [d.page_content for d in docs]
        # Dense 向量（查询前缀由 HuggingFaceBgeEmbeddings 的 embed_documents 处理时不加前缀）
        dense_vecs = self.embeddings.embed_documents(texts)
        # Sparse 向量（BGE-M3 的 encode 方法支持 return_sparse=True）
        sparse_vecs = self._encode_sparse(texts)

        rows = []
        for i, doc in enumerate(docs):
            rows.append({
                "text":       doc.page_content[:4096],
                "dense_vec":  dense_vecs[i],
                "sparse_vec": sparse_vecs[i],
                "source":     doc.metadata.get("source", "unknown"),
                "doc_type":   doc.metadata.get("doc_type", "unknown"),
                "department": doc.metadata.get("department", department),
                "file_hash":  doc.metadata.get("file_hash", ""),
                "created_at": int(time.time()),
            })

        self.client.insert(self.collection, rows)
        logger.info(f"写入 {len(rows)} 条向量到集合 '{self.collection}'")
        return len(rows)

    def delete_by_hash(self, file_hash: str) -> int:
        """删除指定文件的所有 chunk"""
        res = self.client.query(
            self.collection,
            filter=f'file_hash == "{file_hash}"',
            output_fields=["id"],
        )
        ids = [r["id"] for r in res]
        if ids:
            self.client.delete(self.collection, ids=ids)
        return len(ids)

    # ── 检索 ──────────────────────────────────────────

    def hybrid_search(
        self,
        query: str,
        top_k: int = 20,
        department_filter: Optional[str] = None,
    ) -> List[Document]:
        """RRF 混合检索（Dense + Sparse）"""
        expr = f'department == "{department_filter}"' if department_filter else None

        # 查询向量（加 query_instruction 前缀）
        dense_q = self.embeddings.embed_query(query)
        sparse_q = self._encode_sparse([query])[0]

        dense_req = AnnSearchRequest(
            data=[dense_q],
            anns_field="dense_vec",
            param={"metric_type": "COSINE", "params": {"ef": 128}},
            limit=top_k,
            expr=expr,
        )
        sparse_req = AnnSearchRequest(
            data=[sparse_q],
            anns_field="sparse_vec",
            param={"metric_type": "IP"},
            limit=top_k,
            expr=expr,
        )
        results = self.client.hybrid_search(
            self.collection,
            reqs=[dense_req, sparse_req],
            ranker=RRFRanker(k=settings.RRF_K),
            limit=top_k,
            output_fields=["text", "source", "doc_type", "department"],
        )
        docs = []
        for hit in results[0]:
            docs.append(Document(
                page_content=hit.entity.get("text", ""),
                metadata={
                    "source":     hit.entity.get("source", ""),
                    "doc_type":   hit.entity.get("doc_type", ""),
                    "department": hit.entity.get("department", ""),
                    "score":      hit.score,
                },
            ))
        return docs

    # ── 工具方法 ──────────────────────────────────────

    def _encode_sparse(self, texts: List[str]) -> List[dict]:
        """
        使用 FlagEmbedding 的 BGEM3FlagModel 生成稀疏向量。
        若未安装 FlagEmbedding，退化为简单词频 BM25 字典。
        """
        try:
            from FlagEmbedding import BGEM3FlagModel
            model = BGEM3FlagModel(settings.EMBEDDING_MODEL, use_fp16=False)
            outputs = model.encode(texts, return_sparse=True)
            return outputs["lexical_weights"]
        except ImportError:
            logger.warning("FlagEmbedding 未安装，使用简化 BM25 代替稀疏向量")
            return [_simple_bm25(t) for t in texts]

    def get_collection_stats(self) -> dict:
        stats = self.client.get_collection_stats(self.collection)
        return {"collection": self.collection, "row_count": stats.get("row_count", 0)}


def _simple_bm25(text: str) -> dict:
    """降级用的词频稀疏向量（仅供 FlagEmbedding 缺失时使用）"""
    from collections import Counter
    tokens = text.lower().split()
    tf = Counter(tokens)
    total = sum(tf.values())
    return {hash(k) & 0xFFFFFFFF: v / total for k, v in tf.items()}


# 全局单例
_milvus_service: Optional[MilvusService] = None


def get_milvus_service() -> MilvusService:
    global _milvus_service
    if _milvus_service is None:
        _milvus_service = MilvusService()
    return _milvus_service
