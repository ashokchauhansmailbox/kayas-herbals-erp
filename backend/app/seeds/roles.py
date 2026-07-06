"""System roles + role → permission mapping (docs/architecture/05-rbac.md)."""

from __future__ import annotations

from app.seeds.permissions import PERMISSIONS

_ALL = [c for c, _, _ in PERMISSIONS]


def _by_module(module: str) -> list[str]:
    return [c for c, m, _ in PERMISSIONS if m == module]


def _pick(*codes: str) -> list[str]:
    return list(codes)


def _union(*groups: list[str]) -> list[str]:
    seen: dict[str, None] = {}
    for g in groups:
        for c in g:
            seen[c] = None
    return list(seen.keys())


ROLES: list[dict[str, object]] = [
    {
        "code": "super_admin",
        "name": "Super Admin",
        "description": "Full access. Cannot be deleted or suspended (last one protection at service layer).",
        "is_system": True,
        "permissions": _ALL,
    },
    {
        "code": "catalog_manager",
        "name": "Catalog Manager",
        "description": "Owns products, categories, HSN, brands, images, documents, certifications.",
        "is_system": True,
        "permissions": _union(
            _pick(
                "master_data.read",
                "hsn.manage",
                "categories.manage",
                "brands.manage",
                "units.manage",
            ),
            _by_module("catalog"),
        ),
    },
    {
        "code": "inventory_manager",
        "name": "Inventory Manager",
        "description": "Owns warehouses, stock, batches, transfers, alerts.",
        "is_system": True,
        "permissions": _union(
            _pick(
                "master_data.read",
                "warehouses.manage",
                "products.read",
                "variants.manage",
            ),
            _by_module("inventory"),
            _pick("reports.inventory"),
        ),
    },
    {
        "code": "sales_manager",
        "name": "Sales Manager",
        "description": "Orders, distributor pricing, quotes, returns approval, refunds initiation.",
        "is_system": True,
        "permissions": _union(
            _pick(
                "master_data.read",
                "products.read",
                "variants.manage",
                "prices.read",
                "prices.update",
            ),
            _by_module("orders"),
            _pick(
                "distributors.read",
                "distributors.pricing_manage",
                "distributors.credit_manage",
                "distributors.ledger_read",
                "shipments.read",
                "shipments.manage",
                "returns.read",
                "returns.approve",
                "invoices.read",
                "invoices.issue",
                "reports.sales",
                "reports.distributor",
            ),
        ),
    },
    {
        "code": "finance_manager",
        "name": "Finance Manager",
        "description": "Invoices, credit/debit notes, payments, reconciliation, GST exports, audit.",
        "is_system": True,
        "permissions": _union(
            _pick(
                "master_data.read",
                "gst.manage",
                "hsn.manage",
                "tax_rules.manage",
                "payment_terms.manage",
            ),
            _by_module("invoices"),
            _by_module("payments"),
            _by_module("finance"),
            _pick(
                "distributors.read",
                "distributors.kyc_verify",
                "distributors.credit_manage",
                "distributors.ledger_read",
                "vendor_invoices.manage",
                "reports.sales",
                "reports.gst",
                "audit.read",
            ),
        ),
    },
    {
        "code": "support_exec",
        "name": "Support Executive",
        "description": "Tickets, returns handling, refund initiation, review moderation assist.",
        "is_system": True,
        "permissions": _pick(
            "master_data.read",
            "products.read",
            "orders.read",
            "orders.cancel",
            "orders.refund",
            "returns.read",
            "returns.approve",
            "shipments.read",
            "customers.read",
            "tickets.read",
            "tickets.manage",
            "reviews.moderate",
        ),
    },
    {
        "code": "marketing_manager",
        "name": "Marketing Manager",
        "description": "Coupons, campaigns, banners, newsletters, reviews moderation.",
        "is_system": True,
        "permissions": _union(
            _pick("master_data.read", "products.read"),
            _by_module("marketing"),
            _pick("reports.sales"),
        ),
    },
    {
        "code": "distributor",
        "name": "Distributor / Seller",
        "description": "Own KYC, own orders, own ledger, tier price-list view.",
        "is_system": True,
        "permissions": _pick(
            "products.read",
            "prices.read",
            "customers.read",
            "orders.read",
            "orders.create",
            "orders.cancel",
            "invoices.read",
            "shipments.read",
            "returns.read",
            "distributors.ledger_read",
            "tickets.read",
            "tickets.manage",
        ),
    },
    {
        "code": "customer",
        "name": "Customer",
        "description": "Own profile, own orders, wallet, tickets. Public catalog is accessible without login.",
        "is_system": True,
        "permissions": _pick(
            "products.read",
            "prices.read",
            "customers.read",
            "orders.read",
            "orders.create",
            "orders.cancel",
            "invoices.read",
            "shipments.read",
            "returns.read",
            "tickets.read",
            "tickets.manage",
        ),
    },
]


def get_role(code: str) -> dict[str, object]:
    for r in ROLES:
        if r["code"] == code:
            return r
    raise KeyError(code)
