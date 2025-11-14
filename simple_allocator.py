# simple_allocator.py
from typing import Dict, Any
import uuid


class SimpleRuntimeAllocator:
    """
    Simple runtime allocator for Docker Compose setup.
    Points all users to the same runtime container.
    """

    def __init__(self, runtime_url: str = "http://runtime:8001"):
        self.runtime_url = runtime_url

    def allocate(self, user_signature: Dict[str, Any]) -> Dict[str, Any]:
        # Generate or use existing user ID
        user_id = user_signature.get("user_id")
        if not user_id:
            user_id = f"anon-{str(uuid.uuid4())[:8]}"

        # Feature selection based on user signature
        features = ["basic"]
        if user_signature.get("has_advanced_cookie"):
            features.append("advanced")

        # In a real implementation, this might select different runtime URLs
        # based on user needs, load balancing, etc.
        return {
            "runtime_url": self.runtime_url,
            "user_id": user_id,
            "features": features,
            "runtime_id": "runtime-01",  # Static for this POC
        }
