"""
RAG 核心服务
- 三层分块策略（规则 / 语义 / ParentDocumentRetriever）
- BGE-Reranker-v2-m3 精排
- LangChain LCEL RAG Chain（含对话历史）
- 流式输出支持
"""
from __future__ import annotations

import logging
from typing import AsyncIterator, List

from langchain.schema import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.retrievers.document_compressors import CrossEncoderReranker
from langchain.retrievers import ContextualCompressionRetriever
from langchain_community.cross_encoders import HuggingFaceCrossEncoder
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough, RunnableParallel
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_community.chat_message_histories import RedisChatMessageHistory
from langchain_openai import ChatOpenAI

from app.core.config import settings
from app.services.milvus_service import get_milvus_service

logger = logging.getLogger(__name__)


# ── Prompt 模板 ────────────────────────────────────────────────────────────────

SYSTEM_PROMPT = """你是一名专业的企业内部知识库助手。
请严格根据以下检索到的文档内容回答用户问题，不得凭空推断或编造信息。
如果文档中没有足够信息，请明确说明"根据现有文档，暂无相关信息，建议联系对应部门确认"。

回答要求：
- 语言简洁专业，结构清晰
- 涉及政策、规定时注明文档来源
- 数字、日期等关键信息保持准确

参考文档：
{context}

当前日期：{current_date}"""

QA_PROMPT = ChatPromptTemplate.from_messages([
    ("system", SYSTEM_PROMPT),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])

CONTEXTUALIZE_Q_PROMPT = ChatPromptTemplate.from_messages([
    ("system",
     "给定对话历史和最新用户问题，将最新问题改写为不依赖历史的独立问题。"
     "如果问题已经独立，直接返回原问题，不要回答问题本身。"),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


class RAGService:
    """RAG 核心服务，单例模式"""

    def __init__(self):
        self.milvus = get_milvus_service()
        self._llm = self._build_llm()
        self._reranker = self._build_reranker()
        self._splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.CHUNK_SIZE,
            chunk_overlap=settings.CHUNK_OVERLAP,
            separators=["\n\n", "\n", "。", "，", ".", " ", ""],
        )
        self._chain = self._build_chain()

    # ── 构建组件 ───────────────────────────────────────

    def _build_llm(self) -> ChatOpenAI:
        return ChatOpenAI(
            model=settings.LLM_MODEL,
            api_key=settings.LLM_API_KEY,
            base_url=settings.LLM_BASE_URL,
            temperature=settings.LLM_TEMPERATURE,
            max_tokens=settings.LLM_MAX_TOKENS,
            streaming=True,
        )

    def _build_reranker(self) -> ContextualCompressionRetriever:
        cross_encoder = HuggingFaceCrossEncoder(
            model_name=settings.RERANKER_MODEL,
            model_kwargs={"device": settings.RERANKER_DEVICE},
        )
        compressor = CrossEncoderReranker(
            model=cross_encoder,
            top_n=settings.RERANKER_TOP_N,
        )

        class MilvusRetriever:
            """将 MilvusService.hybrid_search 包装为 LangChain BaseRetriever 接口"""
            def __init__(self, svc, top_k):
                self.svc = svc
                self.top_k = top_k

            def get_relevant_documents(self, query: str, **kwargs) -> List[Document]:
                return self.svc.hybrid_search(query, top_k=self.top_k)

            async def aget_relevant_documents(self, query: str, **kwargs) -> List[Document]:
                return self.get_relevant_documents(query)

        base_retriever = MilvusRetriever(self.milvus, settings.RETRIEVAL_TOP_K)
        return ContextualCompressionRetriever(
            base_compressor=compressor,
            base_retriever=base_retriever,
        )

    def _build_chain(self) -> RunnableWithMessageHistory:
        from datetime import date

        def format_docs(docs: List[Document]) -> str:
            return "\n\n---\n\n".join([
                f"【来源：{d.metadata.get('source', '未知')}】\n{d.page_content}"
                for d in docs
            ])

        # 问题改写链（利用对话历史消歧）
        contextualize_chain = CONTEXTUALIZE_Q_PROMPT | self._llm | StrOutputParser()

        def get_context(inputs: dict) -> str:
            history = inputs.get("chat_history", [])
            question = inputs["input"]
            if history:
                standalone_q = contextualize_chain.invoke(inputs)
            else:
                standalone_q = question
            docs = self._reranker.get_relevant_documents(standalone_q)
            return format_docs(docs)

        rag_chain = (
            RunnableParallel({
                "context":      get_context,
                "input":        lambda x: x["input"],
                "chat_history": lambda x: x.get("chat_history", []),
                "current_date": lambda _: date.today().isoformat(),
            })
            | QA_PROMPT
            | self._llm
            | StrOutputParser()
        )

        return RunnableWithMessageHistory(
            rag_chain,
            lambda session_id: RedisChatMessageHistory(
                session_id, url=settings.REDIS_URL
            ),
            input_messages_key="input",
            history_messages_key="chat_history",
        )

    # ── 对外接口 ───────────────────────────────────────

    async def astream_answer(
        self, question: str, session_id: str = "default"
    ) -> AsyncIterator[str]:
        """流式生成答案"""
        async for chunk in self._chain.astream(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        ):
            if isinstance(chunk, str):
                yield chunk

    def get_answer(self, question: str, session_id: str = "default") -> str:
        """同步获取答案（用于测试）"""
        return self._chain.invoke(
            {"input": question},
            config={"configurable": {"session_id": session_id}},
        )

    # ── 文档处理 ───────────────────────────────────────

    def process_and_index(
        self, docs: List[Document], department: str = "general"
    ) -> int:
        """分块 → 向量化 → 写入 Milvus，返回写入条数"""
        if not docs:
            return 0
        # 检查是否已入库
        file_hash = docs[0].metadata.get("file_hash", "")
        if file_hash and self.milvus.hash_exists(file_hash):
            logger.info(f"文件 {file_hash} 已存在，跳过入库")
            return 0

        chunks = self._splitter.split_documents(docs)
        for chunk in chunks:
            chunk.metadata["department"] = department

        return self.milvus.add_documents(chunks, department=department)

    def search(self, query: str, top_k: int = 5) -> List[Document]:
        """直接语义检索（不经过 LLM）"""
        return self._reranker.get_relevant_documents(query)[:top_k]


# 全局单例
_rag_service: RAGService | None = None


def get_rag_service() -> RAGService:
    global _rag_service
    if _rag_service is None:
        _rag_service = RAGService()
    return _rag_service
