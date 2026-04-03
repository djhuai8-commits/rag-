"""
问答接口
POST /api/chat/stream  — SSE 流式问答
POST /api/chat/ask     — 同步问答（用于测试）
GET  /api/chat/history — 获取会话历史
DELETE /api/chat/history/{session_id} — 清空会话
"""
import json
import logging
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse

from app.core.security import get_current_user
from app.schemas.chat import ChatRequest
from app.services.rag_service import get_rag_service

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/chat", tags=["问答"])


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """SSE 流式问答接口"""
    rag = get_rag_service()

    async def generate():
        try:
            async for chunk in rag.astream_answer(
                question=request.question,
                session_id=f"{current_user['username']}:{request.session_id}",
            ):
                data = json.dumps({"type": "token", "content": chunk}, ensure_ascii=False)
                yield f"data: {data}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"
        except Exception as e:
            logger.error(f"流式问答异常：{e}")
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "X-Accel-Buffering": "no",
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        },
    )


@router.post("/ask")
async def chat_ask(
    request: ChatRequest,
    current_user: dict = Depends(get_current_user),
):
    """同步问答接口（用于调试）"""
    rag = get_rag_service()
    answer = rag.get_answer(
        question=request.question,
        session_id=f"{current_user['username']}:{request.session_id}",
    )
    return {"question": request.question, "answer": answer}


@router.delete("/history/{session_id}")
async def clear_history(
    session_id: str,
    current_user: dict = Depends(get_current_user),
):
    """清空指定会话历史"""
    from langchain_community.chat_message_histories import RedisChatMessageHistory
    from app.core.config import settings

    full_session_id = f"{current_user['username']}:{session_id}"
    history = RedisChatMessageHistory(full_session_id, url=settings.REDIS_URL)
    history.clear()
    return {"message": f"会话 {session_id} 历史已清空"}


@router.post("/search")
async def semantic_search(
    query: str,
    top_k: int = 5,
    current_user: dict = Depends(get_current_user),
):
    """纯语义检索接口（不调用 LLM，用于调试检索效果）"""
    rag = get_rag_service()
    docs = rag.search(query, top_k=top_k)
    return {
        "query": query,
        "results": [
            {
                "content": d.page_content[:500],
                "source": d.metadata.get("source", ""),
                "score": d.metadata.get("score", 0),
            }
            for d in docs
        ],
    }
