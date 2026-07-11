import uuid
from fastapi import Header, HTTPException, Request
from app.services.session import SessionManager
from app.core.redis import redis_client
from app.core.config import settings

async def get_session_id(x_user_id: str = Header(None)) -> str:
    """
    从请求头获取用户 ID，若没有则生成唯一临时 ID。
    """
    if not x_user_id:
        x_user_id = str(uuid.uuid4())
    return f"u{x_user_id}"

async def get_session_manager() -> SessionManager:
    # 直接使用单例，避免每次新建
    return SessionManager()