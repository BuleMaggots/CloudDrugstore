from pydantic import BaseModel

class ChatResponse(BaseModel):
    reply: str
    session_id: str
    need_more_info: bool = False   # 是否还需要继续追问
    collected_info: dict = {}      # 当前已收集的信息
