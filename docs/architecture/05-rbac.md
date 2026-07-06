# 05 — RBAC Design & Permission Matrix

## Model
Capability-based. A **role** owns a set of **permissions**. A **user** holds one or more roles. Effective permissions = UNION of role permissions.

## Permission code convention
`<module>.<action>` — e.g. `products.create`, `orders.refund`, `gst.export`, `users.suspend`.

## System roles (seeded)
| Code | Name | Scope |
|---|---|---|
| `super_admin` | Super Admin | all permissions |
| `catalog_manager` | Catalog Manager | products, categories, HSN, brands, images |
| `inventory_manager` | Inventory Manager | warehouses, stock, batches, transfers, alerts |
| `sales_manager` | Sales Manager | orders, distributor pricing, quotes |
| `finance_manager` | Finance Manager | invoices, credit/debit notes, payments, GST, reconciliation |
| `support_exec` | Support Executive | tickets, returns, refunds (initiate) |
| `marketing_manager` | Marketing Manager | coupons, campaigns, banners, newsletters, reviews moderation |
| `distributor` | Distributor / Seller | own KYC, own orders, own ledger, price-list view |
| `customer` | Customer | own profile, own orders, wallet, tickets |

## Permission matrix (excerpt — full matrix in `05a-permission-matrix.csv`)

| Permission | Super | Catalog | Inv | Sales | Finance | Support | Marketing | Distributor | Customer |
|---|---|---|---|---|---|---|---|---|---|
| `users.create` | ✅ | | | | | | | | |
| `users.invite` | ✅ | | | | | | | | |
| `users.suspend` | ✅ | | | | | | | | |
| `roles.manage` | ✅ | | | | | | | | |
| `products.read` | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | own tier | public |
| `products.create` | ✅ | ✅ | | | | | | | |
| `products.update` | ✅ | ✅ | | | | | | | |
| `products.delete` | ✅ | ✅ | | | | | | | |
| `stock.read` | ✅ | | ✅ | ✅ | ✅ | | | | |
| `stock.adjust` | ✅ | | ✅ | | | | | | |
| `stock.transfer` | ✅ | | ✅ | | | | | | |
| `purchase.manage` | ✅ | | ✅ | | ✅ | | | | |
| `orders.create` | ✅ | | | ✅ | | | | own | own |
| `orders.update_status` | ✅ | | | ✅ | | | | | |
| `orders.cancel` | ✅ | | | ✅ | | ✅ | | own(pending) | own(pending) |
| `invoices.issue` | ✅ | | | ✅ | ✅ | | | | |
| `invoices.void` | ✅ | | | | ✅ | | | | |
| `credit_notes.create` | ✅ | | | | ✅ | ✅ | | | |
| `payments.reconcile` | ✅ | | | | ✅ | | | | |
| `payments.refund` | ✅ | | | | ✅ | ✅(init) | | | |
| `gst.export` | ✅ | | | | ✅ | | | | |
| `distributors.manage` | ✅ | | | ✅ | ✅ | | | | |
| `distributors.kyc_verify` | ✅ | | | | ✅ | | | | |
| `coupons.manage` | ✅ | | | | | | ✅ | | |
| `campaigns.manage` | ✅ | | | | | | ✅ | | |
| `reviews.moderate` | ✅ | | | | | ✅ | ✅ | | |
| `tickets.manage` | ✅ | | | | | ✅ | | own | own |
| `returns.approve` | ✅ | | | ✅ | ✅ | ✅ | | | |
| `reports.sales` | ✅ | | | ✅ | ✅ | | ✅ | own | |
| `reports.inventory` | ✅ | | ✅ | | ✅ | | | | |
| `reports.gst` | ✅ | | | | ✅ | | | | |
| `settings.manage` | ✅ | | | | | | | | |
| `audit.read` | ✅ | | | | ✅ | | | | |

Full ~120 permission codes generated at Sprint 1 into `permissions.seed.json`.

## Enforcement layers
1. **DB (RLS)** — coarse row scoping (own data).
2. **API middleware** — `Depends(require("orders.refund"))` on route.
3. **Service layer** — business invariants (e.g. distributor cannot exceed credit limit even if `orders.create` granted).
4. **UI** — feature flags + `<CanDo perm="orders.refund" />` guards.

## Role composition rules
- Super Admin cannot be deleted; last one cannot be suspended.
- Custom roles can be created by Super Admin only.
- A user holding zero roles → cannot log in (403).
- Effective permission changes take effect on next token refresh (≤ 15 min) or force-refresh via `sessions.revoke`.
