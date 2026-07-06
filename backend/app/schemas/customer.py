"""Pydantic v2 schemas for the Customer module (Sprint 1.4)."""

from __future__ import annotations

from datetime import date
from decimal import Decimal
from typing import Optional
from uuid import UUID

from pydantic import ConfigDict, Field

from app.schemas.common import ORMModel


class CustomerProfileIn(ORMModel):
    """Full write payload for `PATCH /api/v1/me/profile` (also used for create)."""

    model_config = ConfigDict(extra="forbid")

    phone: Optional[str] = Field(default=None, max_length=24)
    dob: Optional[date] = None
    gender: Optional[str] = Field(default=None, pattern="^(male|female|other|undisclosed)$")
    avatar_url: Optional[str] = Field(default=None, max_length=2048)
    marketing_opt_in: Optional[bool] = None
    preferred_language: Optional[str] = Field(default=None, max_length=8)


class CustomerProfileOut(ORMModel):
    id: UUID
    user_id: UUID
    phone: Optional[str]
    dob: Optional[date]
    gender: Optional[str]
    avatar_url: Optional[str]
    marketing_opt_in: bool
    preferred_language: Optional[str]


class AddressIn(ORMModel):
    model_config = ConfigDict(extra="forbid")

    label: str = Field(default="shipping", pattern="^(billing|shipping|other)$")
    recipient_name: str = Field(min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=24)
    line1: str = Field(min_length=1, max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    landmark: Optional[str] = Field(default=None, max_length=255)
    city: str = Field(min_length=1, max_length=128)
    state: str = Field(min_length=1, max_length=128)
    pincode: str = Field(min_length=1, max_length=16)
    country: str = Field(default="IN", min_length=2, max_length=64)
    is_default: bool = False


class AddressPatch(ORMModel):
    model_config = ConfigDict(extra="forbid")

    label: Optional[str] = Field(default=None, pattern="^(billing|shipping|other)$")
    recipient_name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    phone: Optional[str] = Field(default=None, max_length=24)
    line1: Optional[str] = Field(default=None, min_length=1, max_length=255)
    line2: Optional[str] = Field(default=None, max_length=255)
    landmark: Optional[str] = Field(default=None, max_length=255)
    city: Optional[str] = Field(default=None, min_length=1, max_length=128)
    state: Optional[str] = Field(default=None, min_length=1, max_length=128)
    pincode: Optional[str] = Field(default=None, min_length=1, max_length=16)
    country: Optional[str] = Field(default=None, min_length=2, max_length=64)
    is_default: Optional[bool] = None
    is_active: Optional[bool] = None


class AddressOut(ORMModel):
    id: UUID
    user_id: UUID
    label: str
    recipient_name: str
    phone: Optional[str]
    line1: str
    line2: Optional[str]
    landmark: Optional[str]
    city: str
    state: str
    pincode: str
    country: str
    is_default: bool
    is_active: bool


class WalletOut(ORMModel):
    id: UUID
    user_id: UUID
    currency: str
    balance: Decimal
    is_active: bool


__all__ = [
    "CustomerProfileIn",
    "CustomerProfileOut",
    "AddressIn",
    "AddressPatch",
    "AddressOut",
    "WalletOut",
]
