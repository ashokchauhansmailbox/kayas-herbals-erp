"""Pydantic v2 schemas for the Distributor module (Sprint 1.4)."""

from __future__ import annotations

from decimal import Decimal
from typing import Any, Optional
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import ORMModel


class DistributorTierIn(ORMModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=128)
    description: Optional[str] = None
    default_discount_pct: Decimal = Field(default=Decimal("0"), ge=0, le=100)
    sort_order: int = Field(default=0, ge=0)
    is_active: bool = True

    @field_validator("code")
    @classmethod
    def _code_no_whitespace(cls, v: str) -> str:
        if v != v.strip() or " " in v:
            raise ValueError("code must not contain whitespace")
        return v


class DistributorTierPatch(ORMModel):
    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=128)
    description: Optional[str] = None
    default_discount_pct: Optional[Decimal] = Field(default=None, ge=0, le=100)
    sort_order: Optional[int] = Field(default=None, ge=0)
    is_active: Optional[bool] = None


class DistributorTierOut(ORMModel):
    id: UUID
    code: str
    name: str
    description: Optional[str]
    default_discount_pct: Decimal
    sort_order: int
    is_active: bool


class DistributorIn(ORMModel):
    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=32)
    business_name: str = Field(min_length=1, max_length=255)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=24)
    pan: Optional[str] = Field(default=None, max_length=16)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=24)
    address: Optional[dict[str, Any]] = None
    tier_id: Optional[UUID] = None
    primary_user_id: Optional[UUID] = None
    credit_limit: Decimal = Field(default=Decimal("0"), ge=0)
    credit_days: int = Field(default=0, ge=0, le=365)
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("code")
    @classmethod
    def _code_no_whitespace(cls, v: str) -> str:
        if v != v.strip() or " " in v:
            raise ValueError("code must not contain whitespace")
        return v


class DistributorPatch(ORMModel):
    model_config = ConfigDict(extra="forbid")

    business_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=24)
    pan: Optional[str] = Field(default=None, max_length=16)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=24)
    address: Optional[dict[str, Any]] = None
    tier_id: Optional[UUID] = None
    primary_user_id: Optional[UUID] = None
    credit_limit: Optional[Decimal] = Field(default=None, ge=0)
    credit_days: Optional[int] = Field(default=None, ge=0, le=365)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class DistributorOut(ORMModel):
    id: UUID
    code: str
    business_name: str
    legal_name: Optional[str]
    gstin: Optional[str]
    pan: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[dict[str, Any]]
    tier_id: Optional[UUID]
    primary_user_id: Optional[UUID]
    credit_limit: Decimal
    credit_days: int
    current_balance: Decimal
    kyc_status: str
    is_active: bool
    notes: Optional[str]


class KycVerifyIn(ORMModel):
    model_config = ConfigDict(extra="forbid")

    status: str = Field(pattern="^(verified|rejected)$")
    rejection_reason: Optional[str] = Field(default=None, max_length=1024)


__all__ = [
    "DistributorTierIn",
    "DistributorTierPatch",
    "DistributorTierOut",
    "DistributorIn",
    "DistributorPatch",
    "DistributorOut",
    "KycVerifyIn",
]
