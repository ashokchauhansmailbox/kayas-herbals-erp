"""Static master-data seeds — units, GST slabs, HSN codes, categories, brand, warehouse,
payment terms, tax rules, courier partners. **No demo business data.**"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

UNITS: list[dict] = [
    {"code": "pcs", "name": "Pieces"},
    {"code": "g", "name": "Gram"},
    {"code": "kg", "name": "Kilogram"},
    {"code": "ml", "name": "Millilitre"},
    {"code": "l", "name": "Litre"},
    {"code": "box", "name": "Box"},
    {"code": "strip", "name": "Strip"},
    {"code": "bottle", "name": "Bottle"},
]

GST_RATES: list[dict] = [
    {"rate": Decimal("0"), "description": "Exempt / Nil-rated", "effective_from": date(2017, 7, 1)},
    {"rate": Decimal("5"), "description": "GST 5%", "effective_from": date(2017, 7, 1)},
    {"rate": Decimal("12"), "description": "GST 12%", "effective_from": date(2017, 7, 1)},
    {"rate": Decimal("18"), "description": "GST 18%", "effective_from": date(2017, 7, 1)},
    {"rate": Decimal("28"), "description": "GST 28%", "effective_from": date(2017, 7, 1)},
]

# HSN codes for herbal / ayurvedic + cosmetics + food-supplement families.
HSN_CODES: list[dict] = [
    {"code": "3003", "description": "Medicaments (Ayurvedic, herbal) — unmixed products", "gst_rate": Decimal("12")},
    {"code": "3004", "description": "Medicaments (Ayurvedic, herbal) — mixed / retail dose form", "gst_rate": Decimal("12")},
    {"code": "1211", "description": "Plants and parts of plants used primarily in perfumery, pharmacy, insecticidal or fungicidal", "gst_rate": Decimal("5")},
    {"code": "0902", "description": "Tea, whether or not flavoured (unbranded)", "gst_rate": Decimal("5")},
    {"code": "0910", "description": "Ginger, saffron, turmeric, thyme, bay leaves, curry", "gst_rate": Decimal("5")},
    {"code": "1515", "description": "Other fixed vegetable fats and oils (herbal oils)", "gst_rate": Decimal("12")},
    {"code": "1517", "description": "Margarine; edible mixtures / preparations of vegetable fats and oils", "gst_rate": Decimal("18")},
    {"code": "2106", "description": "Food preparations not elsewhere specified", "gst_rate": Decimal("18")},
    {"code": "3304", "description": "Beauty or make-up preparations, skincare (herbal cosmetics)", "gst_rate": Decimal("18")},
    {"code": "3305", "description": "Preparations for use on the hair", "gst_rate": Decimal("18")},
    {"code": "3401", "description": "Soap; organic surface-active products (herbal soaps)", "gst_rate": Decimal("18")},
    {"code": "9804", "description": "All dutiable articles imported by a passenger or a member of a crew as baggage", "gst_rate": Decimal("28")},
]

CATEGORIES: list[dict] = [
    {"name": "Powders", "slug": "powders", "sort_order": 10},
    {"name": "Capsules", "slug": "capsules", "sort_order": 20},
    {"name": "Teas", "slug": "teas", "sort_order": 30},
    {"name": "Skincare", "slug": "skincare", "sort_order": 40},
    {"name": "Oils", "slug": "oils", "sort_order": 50},
    {"name": "Herbs", "slug": "herbs", "sort_order": 60},
]

BRANDS: list[dict] = [
    {
        "name": "Kaya's Herbals",
        "slug": "kayas-herbals",
        "manufacturer": "Kaya's Herbals Pvt. Ltd.",
        "country_of_origin": "India",
    },
]

WAREHOUSES: list[dict] = [
    {
        "code": "KH-BLR-MAIN",
        "name": "KH-Bangalore-Main",
        "gstin": None,
        "address": {
            "city": "Bangalore",
            "state": "Karnataka",
            "country": "India",
            "pincode": "560001",
        },
    },
]

PAYMENT_TERMS: list[dict] = [
    {"code": "ADV", "name": "Advance payment", "days": 0},
    {"code": "COD", "name": "Cash on delivery", "days": 0},
    {"code": "NET7", "name": "Net 7 days", "days": 7},
    {"code": "NET15", "name": "Net 15 days", "days": 15},
    {"code": "NET30", "name": "Net 30 days", "days": 30},
]

TAX_RULES: list[dict] = [
    {
        "code": "INTRA-STD",
        "name": "Intra-state standard (CGST + SGST)",
        "mode": "intra",
        "components": {"cgst_pct": "half", "sgst_pct": "half"},
        "effective_from": date(2017, 7, 1),
    },
    {
        "code": "INTER-STD",
        "name": "Inter-state standard (IGST)",
        "mode": "inter",
        "components": {"igst_pct": "full"},
        "effective_from": date(2017, 7, 1),
    },
    {
        "code": "EXEMPT",
        "name": "Exempt supply",
        "mode": "exempt",
        "components": {},
        "effective_from": date(2017, 7, 1),
    },
    {
        "code": "ZERO",
        "name": "Zero-rated supply",
        "mode": "zero",
        "components": {},
        "effective_from": date(2017, 7, 1),
    },
]

COURIER_PARTNERS: list[dict] = [
    {"code": "delhivery", "name": "Delhivery", "api_config": {}},
    {"code": "bluedart", "name": "BlueDart", "api_config": {}},
    {"code": "indiapost", "name": "India Post", "api_config": {}},
    {"code": "shiprocket", "name": "Shiprocket", "api_config": {}},
    {"code": "dtdc", "name": "DTDC", "api_config": {}},
]
