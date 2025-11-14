# docker_allocator.py
import docker
import time
from typing import Dict, Any, Optional

from runtime_registry import RuntimeRegistry


class DockerRuntimeAllocator:
    """
    Orchestrates per-user runtime containers.
    - Finds or launches containers
    - Uses labels to associate a container with a user
    """

    def __init__(
        self,
        image_name: str = "my-runtime-image:latest",
        internal_port: int = 8001,
        base_host: str = "localhost",
        registry: Optional[RuntimeRegistry] = None,
    ):
        self.client = docker.from_env()
        self.image_name = image_name
        self.internal_port = internal_port
        self.base_host = base_host
        self.registry = registry or RuntimeRegistry()

    # ------------------------------
    # Container lookup
    # ------------------------------
    def _find_existing_container(self, user_id: str):
        containers = self.client.containers.list(
            filters={
                "label": f"rbt.user_id={user_id}"
            }
        )
        if containers:
            return containers[0]
        return None

    # ------------------------------
    # Container startup
    # ------------------------------
    def _start_container(self, user_id: str, feature_set: Any) -> Dict[str, Any]:
        """
        Starts a container with labels identifying the user
        """
        container_name = f"rbt-runtime-{user_id}"

        # Each container gets host port assigned dynamically
        # Let Docker pick free host port; retrieve after start.
        container = self.client.containers.run(
            self.image_name,
            detach=True,
            name=container_name,
            labels={
                "rbt.managed": "1",
                "rbt.user_id": user_id,
                "rbt.features": ",".join(feature_set),
            },
            ports={f"{self.internal_port}/tcp": None},  # docker chooses free port
        )

        # Give FastAPI time to boot up inside the container
        time.sleep(0.2)

        container.reload()  # refresh network settings
        port_info = container.attrs["NetworkSettings"]["Ports"]
        host_port = port_info[f"{self.internal_port}/tcp"][0]["HostPort"]

        runtime_url = f"http://{self.base_host}:{host_port}"

        runtime_info = {
            "user_id": user_id,
            "container_id": container.id,
            "runtime_url": runtime_url,
            "features": feature_set,
        }

        # Store in registry
        self.registry.set(user_id, runtime_info)
        return runtime_info

    # ------------------------------
    # Main allocate() method
    # ------------------------------
    def allocate(self, user_signature: Dict[str, Any]) -> Dict[str, Any]:
        # 1. Determine user identity
        user_id = user_signature.get("user_id")
        if not user_id:
            # fallback for anonymous sessions
            import uuid
            user_id = f"anon-{uuid.uuid4()}"

        # 2. Look up existing runtime
        existing = self.registry.get(user_id)
        if existing:
            return existing

        # 3. Feature selection
        features = ["basic"]
        if user_signature.get("has_advanced_cookie"):
            features.append("advanced")

        # 4. Check if an actual Docker container already exists (e.g., restarted gateway)
        container = self._find_existing_container(user_id)
        if container:
            container.reload()
            port_info = container.attrs["NetworkSettings"]["Ports"]
            host_port = port_info[f"{self.internal_port}/tcp"][0]["HostPort"]
            runtime_url = f"http://{self.base_host}:{host_port}"

            runtime_info = {
                "user_id": user_id,
                "container_id": container.id,
                "runtime_url": runtime_url,
                "features": features,
            }
            self.registry.set(user_id, runtime_info)
            return runtime_info

        # 5. No existing runtime → create a new one
        return self._start_container(user_id, features)

