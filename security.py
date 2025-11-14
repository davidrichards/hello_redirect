# security.py
import os
import base64
import json
from datetime import datetime, timedelta, timezone
from typing import Dict, Any

import jwt
from cryptography.fernet import Fernet, InvalidToken as FernetInvalidToken


# In real life, load these from env or secret manager
JWT_SIGNING_SECRET = os.environ.get("JWT_SIGNING_SECRET", "dev-signing-secret-change-me")
FERNET_KEY = os.environ.get("FERNET_KEY")

if not FERNET_KEY:
    # For dev only. In prod, generate once and store safely.
    FERNET_KEY = Fernet.generate_key().decode("ascii")

fernet = Fernet(FERNET_KEY.encode("ascii")) if isinstance(FERNET_KEY, str) else Fernet(FERNET_KEY)


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def create_nested_token(
    subject: str,
    claims: Dict[str, Any],
    lifetime_seconds: int = 300,
) -> str:
    """
    1. Create a signed JWT (JWS) with PyJWT.
    2. Encrypt that JWS string with Fernet (AEAD).
    
    Result: opaque string safe to hand to the browser,
    but only your services can decrypt & verify it.
    """
    now = _now_utc()
    payload = {
        "sub": subject,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=lifetime_seconds)).timestamp()),
        **claims,
    }

    # Step 1: Sign (JWS)
    jws = jwt.encode(
        payload,
        JWT_SIGNING_SECRET,
        algorithm="HS256",  # swap to RS256 with public/private keys later if desired
    )

    # jwt.encode returns string in recent PyJWT; ensure bytes for encryption
    if isinstance(jws, str):
        jws_bytes = jws.encode("utf-8")
    else:
        jws_bytes = jws

    # Step 2: Encrypt (JWE-style)
    encrypted = fernet.encrypt(jws_bytes)

    # Return as url-safe str
    return encrypted.decode("ascii")


class TokenValidationError(Exception):
    pass


def decode_nested_token(token: str) -> Dict[str, Any]:
    """
    1. Decrypt the Fernet token to recover the signed JWT.
    2. Verify the JWT signature and expiration.
    3. Return the claims.
    """
    try:
        encrypted_bytes = token.encode("ascii")
        jws_bytes = fernet.decrypt(encrypted_bytes)
    except (FernetInvalidToken, ValueError) as e:
        raise TokenValidationError("Invalid encrypted token") from e

    jws = jws_bytes.decode("utf-8")

    try:
        claims = jwt.decode(
            jws,
            JWT_SIGNING_SECRET,
            algorithms=["HS256"],
        )
    except jwt.ExpiredSignatureError as e:
        raise TokenValidationError("Token expired") from e
    except jwt.InvalidTokenError as e:
        raise TokenValidationError("Invalid token") from e

    return claims

