# runtime_registry.py
from typing import Optional, Dict

class RuntimeRegistry:
    """
    Simple in-memory registry.
    Replace with Redis or PostgreSQL when scaling.
    """
    def __init__(self):
        self._store: Dict[str, Dict] = {}  # user_id → runtime_info

    def get(self, user_id: str) -> Optional[Dict]:
        return self._store.get(user_id)

    def set(self, user_id: str, runtime_info: Dict):
        self._store[user_id] = runtime_info

    def remove(self, user_id: str):
        self._store.pop(user_id, None)

    def all(self):
        return list(self._store.values())

