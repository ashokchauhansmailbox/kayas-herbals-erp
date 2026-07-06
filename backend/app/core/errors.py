import uuid
from typing import cast

from fastapi import HTTPException, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from .logging import log


class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details=None):
        self.code, self.message, self.status, self.details = (
            code,
            message,
            status,
            details or {},
        )


def _envelope(code, message, details, request_id, status):
    return JSONResponse(
        status_code=status,
        content={
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": request_id,
            }
        },
    )


async def domain_handler(request: Request, exc: Exception) -> JSONResponse:
    e = cast(DomainError, exc)
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    log.warning("domain_error", code=e.code, rid=rid)
    return _envelope(e.code, e.message, e.details, rid, e.status)


async def http_handler(request: Request, exc: Exception) -> JSONResponse:
    e = cast(HTTPException, exc)
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    return _envelope("http_error", str(e.detail), {}, rid, e.status_code)


async def validation_handler(request: Request, exc: Exception) -> JSONResponse:
    e = cast(RequestValidationError, exc)
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    # `e.errors()` may include ctx.error objects (raw ValueError from
    # field_validators) that are not JSON-serialisable — pass through
    # `jsonable_encoder` to coerce those into strings.
    details = jsonable_encoder(e.errors())
    return _envelope("validation_error", "Invalid input", details, rid, 422)


async def unhandled(request: Request, exc: Exception) -> JSONResponse:
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    log.exception("unhandled", rid=rid)
    return _envelope("internal_error", "Something went wrong", {}, rid, 500)
