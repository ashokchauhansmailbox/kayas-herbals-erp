# Kaya's Herbals ERP & E-Commerce — PRD

## Original Problem Statement
Create a new project — Kaya's Herbals ERP & E-Commerce. A centralized ERP and E-commerce platform for Kaya's Herbals to manage products, inventory, distributors, billing, GST, customer orders and reports from one dashboard.

## User Choices (defaults applied)
- Auth: JWT-based custom auth (admin, staff, distributor, customer)
- Payments: COD / mock (no gateway yet)
- ERP modules: all — Products, Inventory, Distributors, Orders, Invoices+GST, Reports
- Uploads: image URLs (object storage deferred)
- Design: earthy organic aesthetic (design_agent-driven)

## User Personas
1. **Admin / Staff** — manages catalog, inventory, distributors, orders, invoices, reports
2. **Distributor** — logs in to place bulk orders at tiered pricing
3. **Retail Customer** — browses storefront, adds to cart, checks out with COD

## Architecture
- **Backend**: FastAPI + Motor (Mongo) + JWT (PyJWT) + bcrypt. Routes all under `/api`.
- **Frontend**: React 19 + React Router 7 + Shadcn/UI + Tailwind + Recharts.
- **Auth**: Access token in httpOnly cookie + Bearer header (dual mode).
- **DB collections**: `users`, `products`, `distributors`, `orders`, `invoices`.

## Implemented (2026-02-06)
- JWT auth (login/register/logout/me) with role-based access, admin seeded
- Products CRUD + stock adjustment endpoint
- Distributors CRUD with tiered pricing (silver/gold/platinum + discount %)
- Orders (public checkout + admin listing + status transitions), auto stock decrement
- GST-compliant Invoices with CGST/SGST split (intrastate) & IGST (interstate)
- Reports: dashboard KPIs + daily sales aggregation + top products + low-stock alerts
- Categories endpoint
- Storefront: Landing, Shop, Product detail, Cart, Checkout, Order confirmation, My orders
- Admin Dashboard: Overview + Products + Inventory + Distributors + Orders + Invoices + Reports
- 6 seeded sample products, admin user seeded
- Design language: Cormorant Garamond + Manrope + IBM Plex Sans + JetBrains Mono, moss/terracotta/sand palette

## Backlog

### P0 (next up)
- Payment gateway integration (Razorpay recommended for INR/GST)
- Product image upload via object storage
- Password reset flow

### P1
- Distributor self-service portal (place orders at tier price directly)
- PDF invoice download (currently browser print)
- Batch/expiry tracking per product (herbal shelf life)
- Multi-warehouse inventory
- Email notifications (order confirmation, shipping updates)

### P2
- Advanced analytics (category performance, distributor leaderboard)
- Coupon codes / promotions
- Customer wishlists & reviews
- Multi-currency / language

## Credentials
See `/app/memory/test_credentials.md`
