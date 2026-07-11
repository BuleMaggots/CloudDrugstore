from fastapi import APIRouter, Depends
from app.core.redis import redis_client

router = APIRouter()

@router.get("/health")
async def health_check():
    # 检查 Redis 连接
    try:
        await redis_client.ping()
        redis_status = "ok"
    except Exception:
        redis_status = "failed"
    return {
        "status": "ok",
        "redis": redis_status,
        "service": "agent-api"
    }