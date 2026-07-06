"""Static permission catalogue.

Every capability the platform enforces. `code` follows `<module>.<action>`.
Grouped by module for readability. This list is the source of truth for
migration `dm_006_seed_static.py` — DO NOT reorder or rename without an ADR.
"""

from __future__ import annotations

PERMISSIONS: list[tuple[str, str, str]] = [
    # (code, module, description)
    # ---------- users / identity ----------
    ("users.read", "users", "View users list and detail"),
    ("users.create", "users", "Create a new user (via invitation)"),
    ("users.invite", "users", "Send user invitations"),
    ("users.update", "users", "Update user profile"),
    ("users.suspend", "users", "Suspend an active user"),
    ("users.restore", "users", "Restore a suspended/deleted user"),
    ("users.delete", "users", "Soft-delete a user"),
    ("roles.read", "roles", "View roles and permissions"),
    ("roles.manage", "roles", "Create / update / delete custom roles"),
    ("roles.assign", "roles", "Assign / revoke roles for a user"),
    ("permissions.read", "permissions", "View permission catalogue"),
    ("sessions.read", "sessions", "View own or team sessions"),
    ("sessions.revoke", "sessions", "Revoke a session (force logout)"),
    # ---------- master data ----------
    (
        "master_data.read",
        "master_data",
        "Read master data (units, gst, hsn, brands, warehouses, ...)",
    ),
    ("units.manage", "master_data", "Create / update / delete units"),
    ("gst.manage", "master_data", "Create / update / retire GST rates"),
    ("hsn.manage", "master_data", "Create / update HSN codes"),
    ("categories.manage", "master_data", "Manage category tree"),
    ("brands.manage", "master_data", "Manage brands"),
    ("warehouses.manage", "master_data", "Manage warehouses"),
    ("payment_terms.manage", "master_data", "Manage payment terms"),
    ("tax_rules.manage", "master_data", "Manage tax rules"),
    ("transporters.manage", "master_data", "Manage transporters"),
    ("courier_partners.manage", "master_data", "Manage courier partners"),
    # ---------- catalog ----------
    ("products.read", "catalog", "View products"),
    ("products.create", "catalog", "Create a product"),
    ("products.update", "catalog", "Update a product"),
    ("products.delete", "catalog", "Soft-delete a product"),
    ("variants.manage", "catalog", "Create / update / delete product variants"),
    ("images.manage", "catalog", "Manage product images"),
    ("documents.manage", "catalog", "Manage product documents"),
    ("certifications.manage", "catalog", "Manage product certifications"),
    ("prices.read", "catalog", "View price + purchase-price history"),
    ("prices.update", "catalog", "Change selling price (writes to journal)"),
    # ---------- inventory ----------
    ("stock.read", "inventory", "View stock ledger + snapshots"),
    ("stock.adjust", "inventory", "Post stock adjustments"),
    ("stock.transfer", "inventory", "Post inter-warehouse transfers"),
    ("batches.manage", "inventory", "Manage batches"),
    ("alerts.read", "inventory", "View stock alerts"),
    ("alerts.resolve", "inventory", "Resolve stock alerts"),
    ("valuation.read", "inventory", "View v_stock_valuation"),
    # ---------- purchase (Sprint 1.4) ----------
    ("purchase.read", "purchase", "View purchase orders and vendors"),
    ("purchase.manage", "purchase", "Create / edit purchase orders"),
    ("vendors.manage", "purchase", "Manage vendors"),
    ("grn.manage", "purchase", "Post GRN"),
    ("vendor_invoices.manage", "purchase", "Manage vendor invoices"),
    # ---------- distributors ----------
    ("distributors.read", "distributors", "View distributors"),
    ("distributors.manage", "distributors", "Onboard / update distributors"),
    ("distributors.kyc_verify", "distributors", "Verify distributor KYC"),
    (
        "distributors.pricing_manage",
        "distributors",
        "Manage tier pricing / price lists",
    ),
    ("distributors.credit_manage", "distributors", "Manage distributor credit limits"),
    ("distributors.ledger_read", "distributors", "View distributor ledger"),
    # ---------- customers ----------
    ("customers.read", "customers", "View customer profiles"),
    ("customers.update", "customers", "Update customer profiles"),
    # ---------- orders ----------
    ("orders.read", "orders", "View orders"),
    ("orders.create", "orders", "Create orders"),
    ("orders.update_status", "orders", "Progress order status"),
    ("orders.cancel", "orders", "Cancel an order"),
    ("orders.refund", "orders", "Initiate order refunds"),
    # ---------- invoices ----------
    ("invoices.read", "invoices", "View invoices"),
    ("invoices.issue", "invoices", "Issue invoices"),
    ("invoices.void", "invoices", "Void invoices"),
    ("credit_notes.create", "invoices", "Create credit notes"),
    ("debit_notes.create", "invoices", "Create debit notes"),
    # ---------- payments ----------
    ("payments.read", "payments", "View payments"),
    ("payments.reconcile", "payments", "Reconcile payments"),
    ("payments.refund", "payments", "Refund payments"),
    # ---------- gst / finance ----------
    ("gst.read", "finance", "Read GST reports"),
    ("gst.export", "finance", "Export GSTR-1 / GSTR-3B"),
    # ---------- shipping ----------
    ("shipments.read", "shipping", "View shipments"),
    ("shipments.manage", "shipping", "Book / dispatch shipments"),
    ("returns.read", "shipping", "View returns"),
    ("returns.approve", "shipping", "Approve returns"),
    # ---------- marketing ----------
    ("coupons.manage", "marketing", "Manage coupons"),
    ("campaigns.manage", "marketing", "Manage campaigns"),
    ("banners.manage", "marketing", "Manage banners"),
    ("newsletters.manage", "marketing", "Manage newsletters"),
    ("reviews.moderate", "marketing", "Moderate reviews"),
    # ---------- support ----------
    ("tickets.read", "support", "View tickets"),
    ("tickets.manage", "support", "Manage tickets"),
    # ---------- reports ----------
    ("reports.sales", "reports", "Sales reports"),
    ("reports.inventory", "reports", "Inventory reports"),
    ("reports.gst", "reports", "GST reports"),
    ("reports.distributor", "reports", "Distributor reports"),
    # ---------- settings ----------
    ("settings.read", "settings", "Read settings"),
    ("settings.manage", "settings", "Manage settings + feature flags"),
    ("notifications.manage", "settings", "Manage notification templates"),
    # ---------- audit ----------
    ("audit.read", "audit", "Read audit + activity logs"),
    ("audit.export", "audit", "Export audit logs"),
]


def all_codes() -> list[str]:
    return [c for c, _, _ in PERMISSIONS]
