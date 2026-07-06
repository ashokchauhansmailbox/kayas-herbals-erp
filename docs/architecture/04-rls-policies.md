# 04 — Supabase Row-Level Security (RLS) Policies

## Philosophy
Our FastAPI backend connects with the **service role key** (bypasses RLS) and enforces authZ via our capability-based RBAC. RLS is a **defence-in-depth layer** so that if a client (Supabase JS SDK) ever queries directly, unauthorised rows are still filtered.

## Baseline
- RLS **enabled** on every table.
- Deny-by-default: no policy = no access.
- Backend service role bypasses everything (already exempt).
- Anon key + authenticated key are used only by the storefront for `public.*` read-only views.

## Policies (by group)

### Public reads (storefront browsing)
```sql
-- Public catalog views only
ALTER TABLE products ENABLE ROW LEVEL SECURITY;
CREATE POLICY prod_public_read ON products
  FOR SELECT USING (is_active = true AND deleted_at IS NULL);

ALTER TABLE product_variants ENABLE ROW LEVEL SECURITY;
CREATE POLICY var_public_read ON product_variants
  FOR SELECT USING (
    EXISTS (SELECT 1 FROM products p WHERE p.id = product_id
            AND p.is_active AND p.deleted_at IS NULL)
  );

CREATE POLICY img_public_read ON product_images
  FOR SELECT USING (true);
CREATE POLICY cat_public_read ON categories
  FOR SELECT USING (deleted_at IS NULL);
```

### Self-owned rows (customer)
```sql
CREATE POLICY cust_self ON customer_profiles
  FOR ALL USING (user_id = auth.uid());
CREATE POLICY addr_self ON addresses
  FOR ALL USING (
    owner_type = 'customer'
    AND owner_id = (SELECT id FROM customer_profiles WHERE user_id = auth.uid())
  );
CREATE POLICY orders_self_read ON orders
  FOR SELECT USING (
    customer_id = (SELECT id FROM customer_profiles WHERE user_id = auth.uid())
  );
CREATE POLICY orders_self_insert ON orders
  FOR INSERT WITH CHECK (
    customer_id = (SELECT id FROM customer_profiles WHERE user_id = auth.uid())
  );
```

### Distributor scoping
```sql
CREATE POLICY dist_self ON distributors
  FOR ALL USING (user_id = auth.uid());
CREATE POLICY dist_orders ON orders
  FOR SELECT USING (
    distributor_id = (SELECT id FROM distributors WHERE user_id = auth.uid())
  );
CREATE POLICY dist_ledger ON customer_ledger
  FOR SELECT USING (
    distributor_id = (SELECT id FROM distributors WHERE user_id = auth.uid())
  );
```

### Admin tables
Every operational table (`stock_ledger`, `invoices`, `purchase_orders`, etc.) has:
```sql
CREATE POLICY admin_all ON <table>
  FOR ALL USING (
    EXISTS (
      SELECT 1 FROM user_roles ur
      JOIN roles r ON r.id = ur.role_id
      WHERE ur.user_id = auth.uid()
      AND r.code IN ('super_admin','catalog_manager','inventory_manager','sales_manager','finance_manager')
    )
  );
```
Fine-grained per-permission checks remain in the backend (RLS is coarse safety net).

### Storage policies
- `product-media/*` — public read, authenticated write (backend-issued signed URLs).
- `kyc-docs/*` — no public read; readable only by owner distributor + finance/super_admin roles.
- `invoices/*` — signed URL only, backend generates.

## Testing
Every policy has a paired pytest that:
1. Signs in as user A (customer) → confirms cannot see user B's orders.
2. Signs in as distributor → cannot see admin tables.
3. Anon → sees only public product data.
4. Service role → sees everything.
