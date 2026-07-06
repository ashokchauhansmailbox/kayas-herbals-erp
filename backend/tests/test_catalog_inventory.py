"""Integration + smoke tests for Sprint 1.2 (catalog + inventory).

Runs against DATABASE_URL_TEST_SYNC. Each test operates in a savepoint so
tests don't leak state. Verifies:

    * CRUD on catalog + inventory tables works with the real DDL.
    * BR-INV-06/08 CHECK constraints are enforced by the DB.
    * `v_stock_valuation` view returns computed rows.
    * Journals (`product_price_history`, `purchase_price_history`,
      `stock_ledger`) accept append-only rows and expose them via natural
      indexes.
"""
from __future__ import annotations

import subprocess
import uuid
from decimal import Decimal
from pathlib import Path

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, sessionmaker

BACKEND_DIR = Path(__file__).resolve().parent.parent


def _run_alembic(url: str, *args: str) -> None:
    subprocess.run(
        ["alembic", "-x", f"db_url={url}", *args],
        cwd=BACKEND_DIR,
        check=True,
        capture_output=True,
    )


@pytest.fixture(scope="module")
def db_url(sync_db_url: str) -> str:
    _run_alembic(sync_db_url, "downgrade", "base")
    _run_alembic(sync_db_url, "upgrade", "head")
    yield sync_db_url


@pytest.fixture()
def session(db_url: str):
    engine = create_engine(db_url, future=True)
    factory = sessionmaker(bind=engine, expire_on_commit=False, future=True, class_=Session)
    session = factory()
    try:
        yield session
    finally:
        session.rollback()
        # Wipe rows this test may have written.
        for tbl in (
            "stock_alerts",
            "stock_snapshots",
            "stock_ledger",
            "stock_transfer_items",
            "stock_transfers",
            "stock_adjustments",
            "batches",
            "purchase_price_history",
            "product_price_history",
            "certifications",
            "product_documents",
            "product_images",
            "product_variants",
            "products",
            "warehouses",
            "brands",
            "categories",
            "hsn_codes",
            "gst_rates",
            "units",
        ):
            session.execute(text(f"DELETE FROM {tbl}"))
        session.commit()
        session.close()
        engine.dispose()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _seed_masters(session: Session) -> dict[str, uuid.UUID]:
    """Insert the minimum master-data rows required for catalog + inventory."""
    unit_id = session.execute(
        text(
            "INSERT INTO units (code, name) VALUES (:c, :n) RETURNING id"
        ),
        {"c": f"u-{uuid.uuid4().hex[:6]}", "n": "gram"},
    ).scalar_one()
    gst_id = session.execute(
        text(
            "INSERT INTO gst_rates (rate, effective_from) VALUES (:r, current_date) RETURNING id"
        ),
        {"r": Decimal("5.00")},
    ).scalar_one()
    hsn_id = session.execute(
        text(
            "INSERT INTO hsn_codes (code, default_gst_rate_id) VALUES (:c, :g) RETURNING id"
        ),
        {"c": f"HSN-{uuid.uuid4().hex[:6]}", "g": gst_id},
    ).scalar_one()
    cat_id = session.execute(
        text(
            "INSERT INTO categories (name, slug) VALUES (:n, :s) RETURNING id"
        ),
        {"n": "Powders", "s": f"powders-{uuid.uuid4().hex[:6]}"},
    ).scalar_one()
    brand_id = session.execute(
        text(
            "INSERT INTO brands (name, slug) VALUES (:n, :s) RETURNING id"
        ),
        {"n": f"Kaya-{uuid.uuid4().hex[:6]}", "s": f"kaya-{uuid.uuid4().hex[:6]}"},
    ).scalar_one()
    wh_id = session.execute(
        text(
            "INSERT INTO warehouses (code, name) VALUES (:c, :n) RETURNING id"
        ),
        {"c": f"WH-{uuid.uuid4().hex[:6]}", "n": "Main"},
    ).scalar_one()
    wh2_id = session.execute(
        text(
            "INSERT INTO warehouses (code, name) VALUES (:c, :n) RETURNING id"
        ),
        {"c": f"WH-{uuid.uuid4().hex[:6]}", "n": "Overflow"},
    ).scalar_one()
    session.commit()
    return {
        "unit": unit_id,
        "gst": gst_id,
        "hsn": hsn_id,
        "category": cat_id,
        "brand": brand_id,
        "warehouse_1": wh_id,
        "warehouse_2": wh2_id,
    }


def _seed_product(session: Session, m: dict[str, uuid.UUID]) -> dict[str, uuid.UUID]:
    product_id = session.execute(
        text(
            """
            INSERT INTO products (sku, name, slug, category_id, brand_id, hsn_code_id, default_unit_id, shelf_life_days)
            VALUES (:sku, :n, :s, :c, :b, :h, :u, 730)
            RETURNING id
            """
        ),
        {
            "sku": f"KH-{uuid.uuid4().hex[:6]}",
            "n": "Ashwagandha",
            "s": f"ashwagandha-{uuid.uuid4().hex[:6]}",
            "c": m["category"],
            "b": m["brand"],
            "h": m["hsn"],
            "u": m["unit"],
        },
    ).scalar_one()
    variant_id = session.execute(
        text(
            """
            INSERT INTO product_variants (product_id, sku, variant_name, mrp, base_price, pack_size, unit_id)
            VALUES (:p, :sku, :n, :mrp, :bp, :ps, :u)
            RETURNING id
            """
        ),
        {
            "p": product_id,
            "sku": f"KH-VAR-{uuid.uuid4().hex[:6]}",
            "n": "100g pack",
            "mrp": Decimal("599.00"),
            "bp": Decimal("499.00"),
            "ps": Decimal("100"),
            "u": m["unit"],
        },
    ).scalar_one()
    session.commit()
    return {"product": product_id, "variant": variant_id}


# ---------------------------------------------------------------------------
# Catalog
# ---------------------------------------------------------------------------
def test_can_create_product_with_variant_image_certification_document(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)

    session.execute(
        text(
            "INSERT INTO product_images (variant_id, url, sort_order, is_primary) "
            "VALUES (:v, 'https://cdn/img.png', 0, true)"
        ),
        {"v": p["variant"]},
    )
    session.execute(
        text(
            "INSERT INTO certifications (product_id, type, number, issued_by) "
            "VALUES (:p, 'AYUSH', 'AYU-42', 'Ministry of AYUSH')"
        ),
        {"p": p["product"]},
    )
    session.execute(
        text(
            "INSERT INTO product_documents (product_id, doc_type, title, file_url) "
            "VALUES (:p, 'spec_sheet', 'Ashwagandha spec', 'https://cdn/doc.pdf')"
        ),
        {"p": p["product"]},
    )
    session.commit()

    counts = session.execute(
        text(
            """
            SELECT
              (SELECT count(*) FROM product_variants WHERE product_id = :p),
              (SELECT count(*) FROM product_images WHERE variant_id = :v),
              (SELECT count(*) FROM certifications WHERE product_id = :p),
              (SELECT count(*) FROM product_documents WHERE product_id = :p)
            """
        ),
        {"p": p["product"], "v": p["variant"]},
    ).one()
    assert counts == (1, 1, 1, 1)


def test_product_slug_and_sku_are_unique(session: Session):
    m = _seed_masters(session)
    slug = f"unique-slug-{uuid.uuid4().hex[:6]}"
    sku = f"UNIQ-{uuid.uuid4().hex[:6]}"
    session.execute(
        text(
            "INSERT INTO products (sku, name, slug, category_id) "
            "VALUES (:sku, 'p1', :slug, :c)"
        ),
        {"sku": sku, "slug": slug, "c": m["category"]},
    )
    session.commit()
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO products (sku, name, slug, category_id) "
                "VALUES (:sku, 'p2', :slug, :c)"
            ),
            {"sku": sku, "slug": slug, "c": m["category"]},
        )
        session.commit()


def test_price_history_journal_append_only_shape(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    for price in ("449.00", "479.00", "499.00"):
        session.execute(
            text(
                "INSERT INTO product_price_history (variant_id, price) VALUES (:v, :p)"
            ),
            {"v": p["variant"], "p": Decimal(price)},
        )
    session.commit()
    rows = session.execute(
        text(
            "SELECT price FROM product_price_history WHERE variant_id = :v ORDER BY at"
        ),
        {"v": p["variant"]},
    ).scalars().all()
    assert [str(r) for r in rows] == ["449.00", "479.00", "499.00"]


def test_purchase_price_history_records_without_vendor_fk(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    # vendor_id / po_id are optional and unconstrained (Sprint 1.3 adds FKs).
    fake_vendor = uuid.uuid4()
    fake_po = uuid.uuid4()
    session.execute(
        text(
            """
            INSERT INTO purchase_price_history (variant_id, vendor_id, po_id, price, quantity)
            VALUES (:v, :vendor, :po, :price, :qty)
            """
        ),
        {"v": p["variant"], "vendor": fake_vendor, "po": fake_po, "price": Decimal("250.00"), "qty": Decimal("200")},
    )
    session.commit()
    row = session.execute(
        text("SELECT vendor_id, po_id, price FROM purchase_price_history WHERE variant_id = :v"),
        {"v": p["variant"]},
    ).one()
    assert row.vendor_id == fake_vendor
    assert row.po_id == fake_po
    assert str(row.price) == "250.00"


# ---------------------------------------------------------------------------
# Inventory
# ---------------------------------------------------------------------------
def test_stock_ledger_qty_zero_rejected(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                """
                INSERT INTO stock_ledger (variant_id, warehouse_id, move_type, qty, state_to)
                VALUES (:v, :w, 'inward', 0, 'available')
                """
            ),
            {"v": p["variant"], "w": m["warehouse_1"]},
        )
        session.commit()


def test_stock_transfer_same_warehouse_rejected(session: Session):
    m = _seed_masters(session)
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                """
                INSERT INTO stock_transfers (reference_no, from_warehouse_id, to_warehouse_id)
                VALUES (:r, :w, :w)
                """
            ),
            {"r": f"XF-{uuid.uuid4().hex[:6]}", "w": m["warehouse_1"]},
        )
        session.commit()


def test_stock_snapshot_negative_available_rejected(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                """
                INSERT INTO stock_snapshots (variant_id, warehouse_id, state, qty)
                VALUES (:v, :w, 'available', -5)
                """
            ),
            {"v": p["variant"], "w": m["warehouse_1"]},
        )
        session.commit()


def test_batch_variant_batch_no_uniqueness(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    batch_no = f"B{uuid.uuid4().hex[:6]}"
    session.execute(
        text(
            "INSERT INTO batches (variant_id, batch_no, qty_manufactured) VALUES (:v, :b, 500)"
        ),
        {"v": p["variant"], "b": batch_no},
    )
    session.commit()
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO batches (variant_id, batch_no, qty_manufactured) VALUES (:v, :b, 500)"
            ),
            {"v": p["variant"], "b": batch_no},
        )
        session.commit()


def test_stock_valuation_view_computes_total(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    batch_id = session.execute(
        text(
            "INSERT INTO batches (variant_id, batch_no, qty_manufactured, cost_per_unit, expiry_date) "
            "VALUES (:v, :b, 1000, 12.5000, current_date + INTERVAL '90 days') RETURNING id"
        ),
        {"v": p["variant"], "b": f"BX-{uuid.uuid4().hex[:6]}"},
    ).scalar_one()
    session.execute(
        text(
            """
            INSERT INTO stock_snapshots (variant_id, warehouse_id, batch_id, state, qty)
            VALUES (:v, :w, :b, 'available', 100)
            """
        ),
        {"v": p["variant"], "w": m["warehouse_1"], "b": batch_id},
    )
    session.commit()

    row = session.execute(
        text(
            """
            SELECT qty, cost_per_unit, total_value, days_to_expiry
            FROM v_stock_valuation
            WHERE variant_id = :v AND warehouse_id = :w
            """
        ),
        {"v": p["variant"], "w": m["warehouse_1"]},
    ).one()
    assert row.qty == Decimal("100.0000")
    assert row.cost_per_unit == Decimal("12.5000")
    assert row.total_value == Decimal("1250.0000")
    assert 89 <= row.days_to_expiry <= 91


def test_stock_alert_lifecycle(session: Session):
    m = _seed_masters(session)
    p = _seed_product(session, m)
    session.execute(
        text(
            """
            INSERT INTO stock_alerts
              (alert_type, severity, variant_id, warehouse_id, threshold_value, current_value, message)
            VALUES ('low_stock', 'critical', :v, :w, 20, 5, 'Below threshold')
            """
        ),
        {"v": p["variant"], "w": m["warehouse_1"]},
    )
    session.commit()
    open_row = session.execute(
        text("SELECT id, resolved_at FROM stock_alerts WHERE variant_id = :v"),
        {"v": p["variant"]},
    ).one()
    assert open_row.resolved_at is None
    session.execute(
        text("UPDATE stock_alerts SET resolved_at = now() WHERE id = :i"),
        {"i": open_row.id},
    )
    session.commit()
    resolved = session.execute(
        text("SELECT resolved_at FROM stock_alerts WHERE id = :i"),
        {"i": open_row.id},
    ).scalar_one()
    assert resolved is not None


def test_stock_snapshots_natural_key_uniqueness_with_null_batch(session: Session):
    """Functional unique index uses COALESCE, so NULL batch_id still deduplicates."""
    m = _seed_masters(session)
    p = _seed_product(session, m)
    session.execute(
        text(
            "INSERT INTO stock_snapshots (variant_id, warehouse_id, state, qty) "
            "VALUES (:v, :w, 'available', 10)"
        ),
        {"v": p["variant"], "w": m["warehouse_1"]},
    )
    session.commit()
    with pytest.raises(IntegrityError):
        session.execute(
            text(
                "INSERT INTO stock_snapshots (variant_id, warehouse_id, state, qty) "
                "VALUES (:v, :w, 'available', 5)"
            ),
            {"v": p["variant"], "w": m["warehouse_1"]},
        )
        session.commit()
