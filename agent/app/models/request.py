from pydantic import BaseModel, Field

class ChatRequest(BaseModel):
    message: str = Field(..., min_length=1, max_length=500, description="用户消息")
    reset: bool = Field(False, description="是否重置会话")