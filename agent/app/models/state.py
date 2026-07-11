from typing import List, Optional, Dict, TypedDict

class CollectedInfo(TypedDict):
    """收集到的用户信息"""
    symptoms: List[str]           # 症状列表，如 ["头痛", "发热"]
    age_group: Optional[str]      # 年龄段: child/adolescent/adult/elderly
    allergies: List[str]          # 过敏史，如 ["青霉素"]
    preference: List[str]         # 用药偏好，如 ["中成药", "片剂"]


class ConversationState(TypedDict):
    """智能体对话状态（LangGraph 状态）"""
    # 基础信息
    session_id: str               # 会话ID
    messages: List[Dict[str, str]]  # 消息历史 [{"role": "user/assistant", "content": "..."}]

    # 用户信息
    collected_info: CollectedInfo  # 已收集的结构化信息

    # 意图与流程控制
    intent: str                   # inquiry / chat / other
    confidence: float             # 意图置信度
    need_more_info: bool          # 是否需要继续追问
    pending_question: Optional[str]  # 待追问的问题
    graph_state: str              # 当前图执行阶段: INIT/COLLECTING/FOLLOW_UP/SEARCH/RESULT/DONE

    # 结果
    reply: Optional[str]          # 最终回复内容
    search_results: Optional[List[Dict]]  # 药品检索结果（后续使用）