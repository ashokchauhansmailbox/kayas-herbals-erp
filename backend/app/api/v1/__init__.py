from fastapi import APIRouter

from .routes import health

api_v1 = APIRouter()
api_v1.include_router(health.router, tags=["health"])

# Sprint 1.2+ will add:
#   auth, users, roles, permissions, master_data, audit
# Their route modules do not exist yet; wiring them here would break
# app startup. Each route module MUST be added below when authored.
