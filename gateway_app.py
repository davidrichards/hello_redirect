# gateway_app.py
from typing import Optional, Dict, Any
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import RedirectResponse, JSONResponse

from security import create_nested_token


app = FastAPI(title="Gateway Router")


# --- Runtime allocator setup -----------------------------------------------

import os

# Choose allocator based on environment
USE_DOCKER_ALLOCATOR = os.getenv("USE_DOCKER_ALLOCATOR", "false").lower() == "true"

if USE_DOCKER_ALLOCATOR:
    from docker_allocator import DockerRuntimeAllocator

    allocator = DockerRuntimeAllocator(
        image_name="runtime-service:latest",
        internal_port=8001,
        base_host="localhost",
    )
else:
    from simple_allocator import SimpleRuntimeAllocator

    # Use docker-compose service name or localhost for local development
    runtime_host = os.getenv("RUNTIME_HOST", "runtime")
    runtime_port = os.getenv("RUNTIME_PORT", "8001")
    allocator = SimpleRuntimeAllocator(
        runtime_url=f"http://{runtime_host}:{runtime_port}"
    )


def allocate_runtime(user_signature):
    allocation = allocator.allocate(user_signature)
    return {
        "runtime_host": allocation["runtime_url"],
        "user_id": allocation["user_id"],
        "features": allocation["features"],
        "runtime_id": allocation.get(
            "container_id", allocation.get("runtime_id", "unknown")
        ),
    }


# --- Entry Route ------------------------------------------------------------


@app.get("/")
async def entry(request: Request):
    """
    Entry point:
    - Inspect cookies, headers, IP, etc.
    - Decide which runtime to use
    - Create an encrypted, signed token
    - Redirect the browser to the target runtime
    """
    cookies = request.cookies
    headers = request.headers
    client_host = request.client.host if request.client else "unknown"

    # Minimal 'signature' for now. You can enrich this as much as you like.
    user_signature = {
        "client_ip": client_host,
        "user_agent": headers.get("user-agent"),
        "locale": headers.get("accept-language"),
        "has_advanced_cookie": "rbt_advanced" in cookies,
        "session_cookie": cookies.get("rbt_session"),
        # You might derive or fetch a user_id here
    }

    allocation = allocate_runtime(user_signature)

    # Claims that the runtime needs to know
    token_claims = {
        "user_id": allocation["user_id"],
        "features": allocation["features"],
        "runtime_id": allocation["runtime_id"],
        "origin": "gateway",
    }

    nested_token = create_nested_token(
        subject=allocation["user_id"],
        claims=token_claims,
        lifetime_seconds=300,  # 5 minutes
    )

    # Determine the correct runtime URL based on request source
    runtime_host = allocation["runtime_host"]

    # If request comes from outside Docker (browser), use localhost
    # Check if client is external by looking at forwarded headers or user agent
    is_external_request = (
        request.headers.get("x-forwarded-for") is not None
        or "Mozilla" in headers.get("user-agent", "")
        or "Chrome" in headers.get("user-agent", "")
        or "Safari" in headers.get("user-agent", "")
        or "Firefox" in headers.get("user-agent", "")
        or "Edge" in headers.get("user-agent", "")
    )

    if is_external_request and "runtime:8001" in runtime_host:
        # Replace internal docker network address with localhost for browsers
        runtime_host = runtime_host.replace("runtime:8001", "localhost:8001")

    # You can use query param, path, header, etc. Here we use a query param.
    runtime_url = f"{runtime_host}/start?token={nested_token}"

    return RedirectResponse(url=runtime_url, status_code=307)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "service": "gateway"})
