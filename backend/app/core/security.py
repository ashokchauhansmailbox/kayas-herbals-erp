"""JWT verification + minting for Supabase-issued access tokens.

Verification path (BR-USR-01):
    Authorization: Bearer <jwt>
    → decode with HS256 + SUPABASE_JWT_SECRET
    → verify `aud` == JWT_AUDIENCE (default "authenticated")
    → verify signature + expiry
    → return the claims dict; `sub` becomes the local `users.id`.

Token minting is used ONLY by tests (see tests/factories.py) so we can
produce valid / expired / tampered / wrong-audience tokens without
depending on a live Supabase project.
"""
from __future__ import annotations

import time
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt

from app.core.config import get_settings
from app.core.errors import DomainError


@dataclass(frozen=True)
class TokenClaims:
    sub: uuid.UUID       # subject (Supabase user id)
    email: str | None
    aud: str
    iss: str | None
    exp: int
    iat: int
    jti: str
    raw: dict[str, Any]


class AuthError(DomainError):
    """Raised for every auth failure — mapped to 401 by the exception handler."""

    def __init__(self, code: str, message: str, details: dict | None = None):
        super().__init__(code=code, message=message, status=401, details=details or {})


def _decode(token: str, *, verify_aud: bool = True) -> dict[str, Any]:
    settings = get_settings()
    if not settings.SUPABASE_JWT_SECRET:
        raise AuthError("auth.misconfigured", "JWT secret is not configured")
    try:
        return jwt.decode(
            token,
            settings.SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            audience=settings.JWT_AUDIENCE if verify_aud else None,
            options={"verify_aud": verify_aud, "require": ["exp", "sub"]},
        )
    except jwt.ExpiredSignatureError as exc:
        raise AuthError("auth.token_expired", "Token has expired") from exc
    except jwt.InvalidAudienceError as exc:
        raise AuthError("auth.invalid_audience", "Token audience mismatch") from exc
    except jwt.InvalidIssuerError as exc:
        raise AuthError("auth.invalid_issuer", "Token issuer mismatch") from exc
    except jwt.InvalidSignatureError as exc:
        raise AuthError("auth.invalid_signature", "Token signature invalid") from exc
    except jwt.MissingRequiredClaimError as exc:
        raise AuthError("auth.missing_claim", f"Missing required claim: {exc}") from exc
    except jwt.InvalidTokenError as exc:
        raise AuthError("auth.invalid_token", f"Invalid token: {exc}") from exc


def verify_token(token: str) -> TokenClaims:
    """Decode + validate a Supabase-signed access token."""
    claims = _decode(token, verify_aud=True)
    try:
        sub = uuid.UUID(str(claims["sub"]))
    except (KeyError, ValueError) as exc:
        raise AuthError("auth.invalid_subject", "Token subject is not a UUID") from exc
    return TokenClaims(
        sub=sub,
        email=claims.get("email"),
        aud=claims.get("aud", ""),
        iss=claims.get("iss"),
        exp=int(claims.get("exp", 0)),
        iat=int(claims.get("iat", 0)),
        jti=str(claims.get("jti") or ""),
        raw=claims,
    )


def mint_token(
    *,
    sub: uuid.UUID | str,
    email: str | None = None,
    aud: str | None = None,
    iss: str | None = None,
    ttl_seconds: int = 3600,
    jti: str | None = None,
    extra: dict[str, Any] | None = None,
    secret: str | None = None,
) -> str:
    """Test-only helper: mint a Supabase-shaped token signed with our secret."""
    settings = get_settings()
    now = int(time.time())
    payload: dict[str, Any] = {
        "sub": str(sub),
        "aud": aud or settings.JWT_AUDIENCE,
        "exp": now + ttl_seconds,
        "iat": now,
        "jti": jti or uuid.uuid4().hex,
    }
    if email is not None:
        payload["email"] = email
    if iss is not None:
        payload["iss"] = iss
    if extra:
        payload.update(extra)
    return jwt.encode(payload, secret or settings.SUPABASE_JWT_SECRET, algorithm="HS256")


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def future(seconds: int) -> datetime:
    return utcnow() + timedelta(seconds=seconds)
