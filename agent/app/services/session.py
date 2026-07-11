# app/services/session.py
import json
from typing import Dict
from app.core.redis import redis_client
from datetime import datetime
from app.core.config import settings


class SessionManager:
    def __init__(self):
        self.redis = redis_client
        self.expire = settings.REDIS_EXPIRE_SECONDS

    def _key(self, session_id: str) -> str:
        return f"agent:session:{session_id}"

    async def load(self, session_id: str) -> Dict:
        data = await self.redis.get(self._key(session_id))
        if data:
            return json.loads(data)
        return {
            "session_id": session_id,
            "messages": [],
            "collected_info": {},
            "pending_question": None,
            "graph_state": "INIT"
        }

    async def save(self, session_id: str, state: Dict) -> None:
        state["last_updated"] = datetime.now().isoformat()
        await self.redis.setex(
            self._key(session_id),
            self.expire,
            json.dumps(state, ensure_ascii=False)
        )

    async def clear(self, session_id: str) -> None:
        await self.redis.delete(self._key(session_id))