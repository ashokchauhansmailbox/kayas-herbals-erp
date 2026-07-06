"""Sprint 1.3 API wiring."""

from fastapi import APIRouter

from .routes import audit, auth, health, invitations, users
from .routes.admin import permissions_router, roles_router

api_v1 = APIRouter()
api_v1.include_router(health.router, tags=["health"])
api_v1.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1.include_router(users.router, prefix="/users", tags=["users"])
api_v1.include_router(roles_router, prefix="/roles", tags=["roles"])
api_v1.include_router(permissions_router, prefix="/permissions", tags=["permissions"])
api_v1.include_router(invitations.router, prefix="/invitations", tags=["invitations"])
api_v1.include_router(audit.router, prefix="/audit", tags=["audit"])
