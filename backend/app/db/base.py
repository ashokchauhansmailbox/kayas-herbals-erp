"""Declarative Base with unified naming convention.

Every model MUST inherit from `Base` so Alembic's autogenerate picks it up
and index / constraint names are deterministic across environments.
"""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase


# Alembic + PostgreSQL naming convention (see docs/architecture/03-sqlalchemy-alembic.md).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Shared declarative base. Metadata carries the naming convention."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
