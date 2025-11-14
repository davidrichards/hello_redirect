# runtime_app.py
from fastapi import FastAPI, Request, HTTPException, Query
from fastapi.responses import JSONResponse, HTMLResponse

from security import decode_nested_token, TokenValidationError


app = FastAPI(title="Runtime Service")


@app.get("/start")
async def start(request: Request, token: str = Query(...)):
    """
    Entry point for the runtime.

    - Receives opaque `token` from gateway
    - Decrypts + verifies it
    - Extracts claims (user_id, features, runtime_id, etc.)
    - Sets its own notion of 'session' (cookie, local store, etc.)
    """
    try:
        claims = decode_nested_token(token)
    except TokenValidationError as e:
        raise HTTPException(status_code=401, detail=str(e))

    user_id = claims.get("user_id")
    features = claims.get("features") or []
    runtime_id = claims.get("runtime_id")

    # Here you would:
    # - bind this user_id to a local session
    # - maybe set a cookie with a local session ID
    # - initialize any per-user-per-runtime state
    # For this example, we just return a simple HTML page.

    html = f"""
    <html>
      <head><title>Runtime</title></head>
      <body>
        <h1>Welcome to runtime: {runtime_id}</h1>
        <p>User: {user_id}</p>
        <p>Features: {', '.join(features)}</p>
        <p>Token was verified and decrypted on the server.</p>
        <p>Claim (not safe to expose normally): {claims}</p>
      </body>
    </html>
    """
    return HTMLResponse(content=html)


@app.get("/health")
async def health():
    return JSONResponse({"status": "ok", "service": "runtime"})
