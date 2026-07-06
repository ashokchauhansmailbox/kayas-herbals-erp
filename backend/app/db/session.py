"""Async SQLAlchemy engine + session factory.

Production code uses `async with get_session() as session` (dependency).
Tests may override `_engine` / `_session_factory` via `configure_engine`.
"""

from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import get_settings

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def _build_engine(url: str) -> AsyncEngine:
    settings = get_settings()
    return create_async_engine(
        url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=5,
        echo=settings.APP_ENV == "dev" and settings.LOG_LEVEL == "DEBUG",
        future=True,
    )


def get_engine() -> AsyncEngine:
    global _engine
    if _engine is None:
        _engine = _build_engine(get_settings().DATABASE_URL)
    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    global _session_factory
    if _session_factory is None:
        _session_factory = async_sessionmaker(
            bind=get_engine(),
            expire_on_commit=False,
            autoflush=False,
            class_=AsyncSession,
        )
    return _session_factory


def configure_engine(url: str) -> None:
    """Rebind engine + session factory (used by tests)."""
    global _engine, _session_factory
    _engine = _build_engine(url)
    _session_factory = async_sessionmaker(
        bind=_engine, expire_on_commit=False, autoflush=False, class_=AsyncSession
    )


@asynccontextmanager
async def get_session() -> AsyncIterator[AsyncSession]:
    """FastAPI-friendly async context manager yielding a session with tx boundary."""
    factory = get_session_factory()
    async with factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def dispose_engine() -> None:
    global _engine, _session_factory
    if _engine is not None:
        await _engine.dispose()
    _engine = None
    _session_factory = None
