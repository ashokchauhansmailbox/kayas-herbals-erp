from fastapi import APIRouter
from .routes import auth, users, roles, permissions, master_data, audit, health

api_v1 = APIRouter()
api_v1.include_router(health.router, tags=["health"])
api_v1.include_router(auth.router, prefix="/auth", tags=["auth"])
api_v1.include_router(users.router, prefix="/users", tags=["users"])
api_v1.include_router(roles.router, prefix="/roles", tags=["roles"])
api_v1.include_router(permissions.router, prefix="/permissions", tags=["permissions"])
api_v1.include_router(master_data.router, prefix="/master-data", tags=["master-data"])
api_v1.include_router(audit.router, prefix="/audit", tags=["audit"])
