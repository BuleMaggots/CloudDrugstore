"""
药品检索服务
根据用户症状、年龄、过敏史、偏好等信息从数据库检索合适的药品
"""
import logging
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_, or_, func, text
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.core.database import AsyncSessionLocal
from app.models.drug import Drug, DrugUsage, DrugUsageRelation, DrugUsageSynonym

logger = logging.getLogger(__name__)


async def search_drugs(
    collected_info: Dict[str, Any],
    limit: int = 5
) -> List[Drug]:
    """
    根据用户收集的信息检索药品

    Args:
        collected_info: 包含 symptoms, age_group, allergies, preference 的字典
        limit: 返回的最大药品数量

    Returns:
        按匹配度排序的药品列表（Drug 对象，附加 match_score 属性）
    """
    symptoms = collected_info.get("symptoms", [])
    age_group = collected_info.get("age_group")  # child/adolescent/adult/elderly
    allergies = collected_info.get("allergies", [])
    preference = collected_info.get("preference", [])

    # 如果没有症状，直接返回空
    if not symptoms:
        logger.info("No symptoms provided, returning empty list")
        return []

    async with AsyncSessionLocal() as session:
        # ==================== 第一步：获取所有匹配的用途ID ====================
        usage_ids = await _get_matching_usage_ids(session, symptoms)
        if not usage_ids:
            logger.info(f"No matching usage found for symptoms: {symptoms}")
            return []

        # ==================== 第二步：通过用途ID获取药品ID ====================
        drug_ids = await _get_drug_ids_by_usage_ids(session, usage_ids)
        if not drug_ids:
            logger.info("No drugs found for usage IDs")
            return []

        # ==================== 第三步：查询药品详细信息 ====================
        drugs = await _get_drugs_by_ids(session, drug_ids)
        if not drugs:
            return []

        # ==================== 第四步：过滤与排序 ====================
        # 4.1 过滤年龄（如果有年龄偏好，可以增加过滤逻辑，这里暂不实现）
        # 4.2 过滤过敏（需要成分表，暂不实现）
        # 4.3 计算匹配度
        for drug in drugs:
            # 获取该药品关联的所有用途名称
            usage_names = await _get_usage_names_for_drug(session, drug.id)
            drug.usage_names = usage_names  # 附加属性
            # 匹配度 = 症状与用途名称的交集大小
            match_count = len(set(symptoms) & set(usage_names))
            drug.match_score = match_count

        # 排序：先按匹配度降序，再按销量降序
        drugs.sort(key=lambda d: getattr(d, 'match_score', 0), reverse=True)

        # 返回前 limit 个
        return drugs[:limit]


# ---------- 辅助查询函数 ----------

async def _get_matching_usage_ids(session: AsyncSession, symptoms: List[str]) -> List[int]:
    """
    通过同义词表和用途名称匹配获取用途ID
    """
    usage_ids_set = set()

    # 1. 通过同义词表匹配
    if symptoms:
        synonym_stmt = select(DrugUsageSynonym.usage_id).where(
            DrugUsageSynonym.synonym.in_(symptoms)
        )
        synonym_result = await session.execute(synonym_stmt)
        usage_ids_set.update([row[0] for row in synonym_result])

    # 2. 通过用途名称直接匹配
    if symptoms:
        usage_stmt = select(DrugUsage.id).where(DrugUsage.name.in_(symptoms))
        usage_result = await session.execute(usage_stmt)
        usage_ids_set.update([row[0] for row in usage_result])

    return list(usage_ids_set)


async def _get_drug_ids_by_usage_ids(session: AsyncSession, usage_ids: List[int]) -> List[int]:
    """
    根据用途ID查询关联的药品ID
    """
    if not usage_ids:
        return []

    relation_stmt = select(DrugUsageRelation.drug_id).where(
        DrugUsageRelation.usage_id.in_(usage_ids)
    )
    relation_result = await session.execute(relation_stmt)
    drug_ids = list({row[0] for row in relation_result})  # 去重
    return drug_ids


async def _get_drugs_by_ids(session: AsyncSession, drug_ids: List[int]) -> List[Drug]:
    """
    根据药品ID列表查询药品详细信息（只查上架的）
    """
    if not drug_ids:
        return []

    drug_stmt = select(Drug).options(
        selectinload(Drug.specifications)
    ).where(
        and_(
            Drug.id.in_(drug_ids),
            Drug.status == 1
        )
    )
    drug_result = await session.execute(drug_stmt)
    drugs = drug_result.scalars().all()
    return drugs


async def _get_usage_names_for_drug(session: AsyncSession, drug_id: int) -> List[str]:
    """
    获取某个药品关联的所有用途名称（用于计算匹配度）
    """
    # 关联查询 drug_usage_relation + drug_usage
    stmt = select(DrugUsage.name).join(
        DrugUsageRelation,
        DrugUsageRelation.usage_id == DrugUsage.id
    ).where(DrugUsageRelation.drug_id == drug_id)
    result = await session.execute(stmt)
    return [row[0] for row in result]


# ---------- 直接供 FastAPI 调用的接口（可选） ----------
async def search_drugs_api(
    symptoms: List[str],
    age_group: Optional[str] = None,
    allergies: Optional[List[str]] = None,
    preference: Optional[List[str]] = None,
    limit: int = 5
) -> List[Dict[str, Any]]:
    """
    用于外部API调用的封装，返回字典列表，方便序列化
    """
    collected_info = {
        "symptoms": symptoms,
        "age_group": age_group,
        "allergies": allergies or [],
        "preference": preference or []
    }
    drugs = await search_drugs(collected_info, limit)
    result = []
    for drug in drugs:
        result.append({
            "id": drug.id,
            "name": drug.name,
            "price": float(drug.price) if drug.price else None,
            "description": drug.description,
            "image": drug.image,
            "match_score": getattr(drug, "match_score", 0),
            "specifications": [{"name": spec.name, "value": spec.value} for spec in (drug.specifications or [])]
        })
    return result