"""Pydantic v2 schemas for the Purchase module (Sprint 1.4).

Only the vendor master surface is exposed as HTTP CRUD in Sprint 1.4. The full
PurchaseOrder / GRN / VendorInvoice transactional workflow ships in Sprint 1.5.
"""

from __future__ import annotations

from typing import Any, Optional
from uuid import UUID

from pydantic import ConfigDict, EmailStr, Field, field_validator

from app.schemas.common import ORMModel


class VendorIn(ORMModel):
    """Payload for `POST /api/v1/vendors`."""

    model_config = ConfigDict(extra="forbid")

    code: str = Field(min_length=1, max_length=32)
    name: str = Field(min_length=1, max_length=255)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=24)
    pan: Optional[str] = Field(default=None, max_length=16)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=24)
    address: Optional[dict[str, Any]] = None
    payment_term_id: Optional[UUID] = None
    credit_days: int = Field(default=0, ge=0, le=365)
    currency: str = Field(default="INR", min_length=3, max_length=8)
    is_active: bool = True
    notes: Optional[str] = None

    @field_validator("code")
    @classmethod
    def _code_no_whitespace(cls, v: str) -> str:
        if v != v.strip() or " " in v:
            raise ValueError("code must not contain whitespace")
        return v


class VendorPatch(ORMModel):
    """Partial-update payload for `PATCH /api/v1/vendors/{id}`."""

    model_config = ConfigDict(extra="forbid")

    name: Optional[str] = Field(default=None, min_length=1, max_length=255)
    legal_name: Optional[str] = Field(default=None, max_length=255)
    gstin: Optional[str] = Field(default=None, max_length=24)
    pan: Optional[str] = Field(default=None, max_length=16)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(default=None, max_length=24)
    address: Optional[dict[str, Any]] = None
    payment_term_id: Optional[UUID] = None
    credit_days: Optional[int] = Field(default=None, ge=0, le=365)
    currency: Optional[str] = Field(default=None, min_length=3, max_length=8)
    is_active: Optional[bool] = None
    notes: Optional[str] = None


class VendorOut(ORMModel):
    id: UUID
    code: str
    name: str
    legal_name: Optional[str]
    gstin: Optional[str]
    pan: Optional[str]
    email: Optional[str]
    phone: Optional[str]
    address: Optional[dict[str, Any]]
    payment_term_id: Optional[UUID]
    credit_days: int
    currency: str
    is_active: bool
    notes: Optional[str]


__all__ = ["VendorIn", "VendorPatch", "VendorOut"]
