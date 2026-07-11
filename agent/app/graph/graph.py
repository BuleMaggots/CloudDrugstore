"""
LangGraph 工作流定义
将各个节点连接成完整的多轮对话智能体
"""
from langgraph.graph import StateGraph, END
from app.models.state import ConversationState
from app.graph.nodes import (
    intent_recognition_node,
    info_collection_node,
    follow_up_decision_node,
    drug_search_node,
    result_generation_node,
    handle_chat_node,
    handle_other_node,
)


def route_after_intent(state: ConversationState) -> str:
    """
    根据意图分类路由到不同节点
    """
    intent = state.get("intent", "inquiry")
    if intent == "inquiry":
        return "info_collection"
    elif intent == "chat":
        return "handle_chat"
    else:  # other
        return "handle_other"


def route_after_follow_up(state: ConversationState) -> str:
    """
    根据是否需要继续追问路由
    """
    if state.get("need_more_info", False):
        return END
    else:
        return "drug_search"


def build_agent_graph():
    """
    构建并返回编译后的 LangGraph 图
    """
    # 创建状态图
    workflow = StateGraph(ConversationState)

    # 添加节点
    workflow.add_node("intent_recognition", intent_recognition_node)
    workflow.add_node("info_collection", info_collection_node)
    workflow.add_node("follow_up_decision", follow_up_decision_node)
    workflow.add_node("drug_search", drug_search_node)
    workflow.add_node("result_generation", result_generation_node)
    workflow.add_node("handle_chat", handle_chat_node)
    workflow.add_node("handle_other", handle_other_node)

    # 设置入口
    workflow.set_entry_point("intent_recognition")

    # 条件边：意图识别后分流
    workflow.add_conditional_edges(
        "intent_recognition",
        route_after_intent,
        {
            "info_collection": "info_collection",
            "handle_chat": "handle_chat",
            "handle_other": "handle_other",
        }
    )

    # 信息收集 -> 追问决策
    workflow.add_edge("info_collection", "follow_up_decision")

    # 追问决策后条件边
    workflow.add_conditional_edges(
        "follow_up_decision",
        route_after_follow_up,
        {
            END: END,
            "drug_search": "drug_search",
        }
    )

    # 检索 -> 结果生成
    workflow.add_edge("drug_search", "result_generation")

    # 所有终端节点 -> END
    workflow.add_edge("result_generation", END)
    workflow.add_edge("handle_chat", END)
    workflow.add_edge("handle_other", END)

    # 编译图
    graph = workflow.compile()
    return graph


# 创建全局图实例（单例）
agent_graph = build_agent_graph()


async def run_agent_graph(initial_state: ConversationState) -> ConversationState:
    """
    执行图的入口函数，供 chat 接口调用
    Args:
        initial_state: 初始状态（已包含历史消息和收集信息）
    Returns:
        最终状态
    """
    final_state = await agent_graph.ainvoke(initial_state)
    return final_state