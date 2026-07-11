from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.v1 import chat, health
from app.core.database import engine
from app.core.redis import redis_client
from app.core.config import settings
import os
os.environ["PYDEVD_USE_PEP_669"] = "0"
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动时
    print(f"Starting {settings.APP_NAME} in {settings.APP_ENV} mode")
    # 测试 Redis 连接
    await redis_client.ping()
    # 测试数据库连接
    # async with engine.begin() as conn:
    #     pass
    yield
    # 关闭时
    await redis_client.close()
    await engine.dispose()

app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    debug=settings.DEBUG,
    lifespan=lifespan,
)

# 注册路由
app.include_router(health.router, prefix="/api/v1", tags=["health"])
app.include_router(chat.router, prefix="/api/v1", tags=["chat"])

@app.get("/")
async def root():
    return {"message": f"{settings.APP_NAME} is running"}