from fastapi import APIRouter, Depends, HTTPException
from datetime import datetime
from app.models.request import ChatRequest
from app.models.response import ChatResponse
from app.dependencies.session import get_session_manager, get_session_id
from app.services.session import SessionManager
from app.graph.graph import run_agent_graph
import logging

logger = logging.getLogger(__name__)
router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
async def chat_endpoint(
    request: ChatRequest,
    session_id: str = Depends(get_session_id),
    session_manager: SessionManager = Depends(get_session_manager)
):
    try:
        # 加载会话上下文
        state = await session_manager.load(session_id)

        # 如果请求重置，清空状态
        if request.reset:
            state = {
                "session_id": session_id,
                "messages": [],
                "collected_info": {},
                "pending_question": None,
                "graph_state": "INIT"
            }

        # 追加用户消息
        state["messages"].append({
            "role": "user",
            "content": request.message,
            "timestamp": datetime.now().isoformat()
        })

        # 执行 LangGraph（传入会话管理器和 session_id 以便节点内持久化）
        final_state = await run_agent_graph(state)

        # 提取回复
        reply = final_state.get("reply")
        pending_question = final_state.get("pending_question")

        if pending_question:
            reply = pending_question
            need_more_info = True
        else:
            need_more_info = final_state.get("need_more_info", False)

        if not reply:
            reply = "抱歉，我暂时无法回答您的问题。"
            need_more_info = False
        # 保存更新后的状态
        await session_manager.save(session_id, final_state)

        return ChatResponse(
            reply=reply,
            session_id=session_id,
            need_more_info=need_more_info,
            collected_info=final_state.get("collected_info", {})
        )

    except Exception as e:
        logger.error(f"Chat error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="服务器内部错误")