import json
import re
from langchain_core.messages import HumanMessage, SystemMessage
from app.graph.prompts import (
    INTENT_RECOGNITION_PROMPT,
    INFO_COLLECTION_PROMPT,
    FOLLOW_UP_DECISION_PROMPT,
    RESULT_GENERATION_PROMPT
)
from app.models.state import ConversationState
from app.services.drug_search import search_drugs
from langchain_core.messages import SystemMessage, HumanMessage
from app.dependencies.llm import get_llm

def extract_json(raw_content: str) -> dict:
    """从LLM响应中提取JSON，支持markdown代码块"""
    # 去除可能的 ```json 和 ``` 标记
    cleaned = re.sub(r'```json\s*', '', raw_content)
    cleaned = re.sub(r'```\s*', '', cleaned)
    # 尝试直接解析
    try:
        return json.loads(cleaned.strip())
    except json.JSONDecodeError:
        # 如果仍然失败，尝试提取 { ... } 之间的内容
        match = re.search(r'\{.*\}', cleaned, re.DOTALL)
        if match:
            return json.loads(match.group())
        raise
async def intent_recognition_node(state: ConversationState) -> ConversationState:
    """意图识别：只做分类"""
    # 获取上下文
    print("intent_recognition_node")
    messages = state.get("messages", [])
    user_message = messages[-1]["content"] if messages else ""
    last_assistant = messages[-2]["content"] if len(messages) >= 2 and messages[-2]["role"] == "assistant" else ""

    # ========== 硬规则拦截：问候语直接判为 chat ==========
    greetings = {"你好", "您好", "hi", "hello", "hey", "在吗", "在不在"}
    user_clean = user_message.strip().lower()
    if user_clean in greetings or user_clean.startswith(("你好", "您好")):
        state["intent"] = "chat"
        state["confidence"] = 1.0
        state["graph_state"] = "CHAT"
        print(f"拦截问候语: '{user_message}' -> 直接设置为 chat")
        return state

    # 正常 LLM 调用
    llm = get_llm()
    prompt = INTENT_RECOGNITION_PROMPT.format(
        user_message=user_message,
        last_assistant_message=last_assistant
    )

    response = await llm.ainvoke([
        SystemMessage(content="你是意图识别专家，只输出JSON格式。"),
        HumanMessage(content=prompt)
    ])
    print(f"LLM原始响应: {response.content}")
    try:
        result = json.loads(response.content)
        state["intent"] = result.get("intent", "inquiry")
        state["confidence"] = result.get("confidence", 0.8)
    except Exception as e:
        print(f"意识识别失败: {e},原始类容:{response.content[:100]}")
        state["intent"] = "inquiry"
        state["confidence"] = 0.5

    # 更新图状态：如果意图是inquiry，进入收集模式
    if state["intent"] == "inquiry":
        state["graph_state"] = "COLLECTING"
    else:
        state["graph_state"] = state["intent"].upper()

    return state


async def info_collection_node(state: ConversationState) -> ConversationState:
    """信息收集：提取结构化信息"""
    print("info_collection_node")
    print(state.get("collected_info"))
    llm = get_llm()
    # 获取对话历史（最近10条）
    messages = state.get("messages", [])
    history = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-10:]])

    user_message = messages[-1]["content"] if messages else ""

    prompt = INFO_COLLECTION_PROMPT.format(
        user_message=user_message,
        conversation_history=history,
        existing_collected_info=json.dumps(state.get("collected_info", {}), ensure_ascii=False)
    )

    response = await llm.ainvoke([
        SystemMessage(content="你是信息提取专家，只输出JSON格式。"),
        HumanMessage(content=prompt)
    ])

    try:
        new_info = json.loads(response.content)
        # 合并信息（保留历史 + 本次新增）
        existing = state.get("collected_info", {})
        state["collected_info"] = {
            "symptoms": list(set(existing.get("symptoms", []) + new_info.get("symptoms", []))),
            "age_group": new_info.get("age_group") or existing.get("age_group"),
            "allergies": list(set(existing.get("allergies", []) + new_info.get("allergies", []))),
            "preference": list(set(existing.get("preference", []) + new_info.get("preference", [])))
        }
    except json.JSONDecodeError:
        pass

    state["graph_state"] = "FOLLOW_UP"
    return state


async def follow_up_decision_node(state: ConversationState) -> ConversationState:
    """追问决策：判断是否继续追问"""
    print("follow_up_decision_node")
    llm = get_llm()
    messages = state.get("messages", [])
    last_user = messages[-1]["content"] if messages else ""
    context = "\n".join([f"{m['role']}: {m['content']}" for m in messages[-4:]])

    prompt = FOLLOW_UP_DECISION_PROMPT.format(
        collected_info=json.dumps(state.get("collected_info", {}), ensure_ascii=False),
        last_user_message=last_user,
        context=context
    )

    response = await llm.ainvoke([
        SystemMessage(content="你是追问决策专家，只输出JSON格式。"),
        HumanMessage(content=prompt)
    ])

    try:
        result = json.loads(response.content)
        state["need_more_info"] = result.get("need_more_info", False)
        state["pending_question"] = result.get("next_question")
        # 更新收集信息
        if result.get("collected_info"):
            state["collected_info"] = result["collected_info"]
    except json.JSONDecodeError:
        state["need_more_info"] = False
        state["pending_question"] = None

    return state



async def drug_search_node(state: ConversationState) -> ConversationState:
    """
    药品检索节点：调用 search_drugs，将结果存入状态
    """
    print("drug_search_node")
    collected_info = state.get("collected_info", {})
    drugs = await search_drugs(collected_info, limit=5)
    # 将 Drug 对象转换为可序列化的字典，避免 JSON 序列化失败
    state["search_results"] = [{
        "id": drug.id,
        "name": drug.name,
        "price": float(drug.price) if drug.price else None,
        "description": drug.description,
        "image": drug.image,
        "match_score": getattr(drug, "match_score", 0),
        "specifications": [{"name": spec.name, "value": spec.value} for spec in (drug.specifications or [])]
    } for drug in drugs]
    state["graph_state"] = "SEARCH"
    return state


async def result_generation_node(state: ConversationState) -> ConversationState:
    """
    结果生成节点：基于检索结果和用户信息生成推荐文案
    """
    print("result_generation_node")
    collected_info = state.get("collected_info", {})
    drugs = state.get("search_results", [])

    # 如果无检索结果，直接返回预设回复，不调用 LLM
    if not drugs:
        state["reply"] = "非常抱歉，我没有找到完全匹配您症状的药品。建议您补充更多症状信息，或者咨询线下药师。"
        state["graph_state"] = "DONE"
        return state
    llm = get_llm()
    collected_info = state.get("collected_info", {})
    drugs = state.get("search_results", [])

    # 构造药品信息文本
    if drugs:
        drugs_text = ""
        for i, drug in enumerate(drugs, 1):
            specs = drug.get("specifications", [])
            spec_names = ", ".join([s.get("name", "") for s in specs[:2]]) if specs else "无规格"
            drugs_text += f"""
        {i}. **{drug.get('name', '')}**
           - 规格：{spec_names}
           - 价格：¥{drug.get('price', '')}
           - 功效：{drug.get('description', '') or '暂无描述'}
           - 匹配症状数：{drug.get('match_score', 0)}
        """
    else:
        drugs_text = "（暂无匹配药品）"

    # 构建 Prompt
    prompt = RESULT_GENERATION_PROMPT.format(
        symptoms="、".join(collected_info.get("symptoms", [])),
        age_group=collected_info.get("age_group") or "未知",
        allergies="、".join(collected_info.get("allergies", [])) or "无",
        preference="、".join(collected_info.get("preference", [])) or "无特殊偏好",
        drugs=drugs_text
    )

    # 调用 LLM 生成回复
    response = await llm.ainvoke([
        SystemMessage(content="你是药店智能客服推荐专家，擅长生成清晰、有帮助的药品推荐。"),
        HumanMessage(content=prompt)
    ])

    state["reply"] = response.content
    state["graph_state"] = "DONE"
    state["need_more_info"] = False
    state["pending_question"] = None
    return state


async def handle_chat_node(state: ConversationState) -> ConversationState:
    """处理闲聊意图"""
    state["reply"] = "您好，请问有什么可以帮您的吗？如果您需要药品咨询，请告诉我您的症状。"
    state["graph_state"] = "DONE"
    return state


async def handle_other_node(state: ConversationState) -> ConversationState:
    """处理无关意图"""
    state["reply"] = "抱歉，我主要提供药品咨询和推荐服务，请您描述一下您的症状，我会尽力帮助您。"
    state["graph_state"] = "DONE"
    return state