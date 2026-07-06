from fastapi import Request, HTTPException
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from .logging import log
import uuid

class DomainError(Exception):
    def __init__(self, code: str, message: str, status: int = 400, details=None):
        self.code, self.message, self.status, self.details = code, message, status, details or {}

def _envelope(code, message, details, request_id, status):
    return JSONResponse(status_code=status, content={"error": {"code": code, "message": message, "details": details, "request_id": request_id}})

async def domain_handler(request: Request, exc: DomainError):
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    log.warning("domain_error", code=exc.code, rid=rid)
    return _envelope(exc.code, exc.message, exc.details, rid, exc.status)

async def http_handler(request: Request, exc: HTTPException):
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    return _envelope("http_error", str(exc.detail), {}, rid, exc.status_code)

async def validation_handler(request: Request, exc: RequestValidationError):
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    return _envelope("validation_error", "Invalid input", exc.errors(), rid, 422)

async def unhandled(request: Request, exc: Exception):
    rid = request.headers.get("X-Request-Id", str(uuid.uuid4()))
    log.exception("unhandled", rid=rid)
    return _envelope("internal_error", "Something went wrong", {}, rid, 500)
