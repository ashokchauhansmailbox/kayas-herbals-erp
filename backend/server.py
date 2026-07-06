from dotenv import load_dotenv
from pathlib import Path
ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

import os
import logging
import uuid
import bcrypt
import jwt
from datetime import datetime, timezone, timedelta
from typing import List, Optional, Literal
from fastapi import FastAPI, APIRouter, HTTPException, Request, Response, Depends, Query
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field, EmailStr, ConfigDict

# ---- Config ----
mongo_url = os.environ["MONGO_URL"]
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ["DB_NAME"]]

JWT_SECRET = os.environ["JWT_SECRET"]
JWT_ALGORITHM = "HS256"
ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@kayaherbals.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

app = FastAPI(title="Kaya's Herbals ERP API")
api = APIRouter(prefix="/api")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

# ---- Utils ----
def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def verify_password(pw: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), hashed.encode("utf-8"))
    except Exception:
        return False

def create_access_token(user_id: str, email: str, role: str) -> str:
    payload = {
        "sub": user_id,
        "email": email,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(days=7),
        "type": "access",
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

# ---- Models ----
Role = Literal["admin", "staff", "distributor", "customer"]

class RegisterInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=6)
    name: str = Field(min_length=1)
    role: Role = "customer"
    phone: Optional[str] = None

class LoginInput(BaseModel):
    email: EmailStr
    password: str

class UserOut(BaseModel):
    model_config = ConfigDict(extra="ignore")
    id: str
    email: str
    name: str
    role: Role
    phone: Optional[str] = None
    created_at: str

class ProductIn(BaseModel):
    name: str
    sku: str
    category: str
    description: Optional[str] = ""
    mrp: float
    price: float
    distributor_price: Optional[float] = None
    stock: int = 0
    gst_rate: float = 5.0
    image_url: Optional[str] = ""
    low_stock_threshold: int = 10
    active: bool = True

class ProductOut(ProductIn):
    id: str
    created_at: str

class DistributorIn(BaseModel):
    name: str
    email: EmailStr
    phone: str
    company: Optional[str] = ""
    gstin: Optional[str] = ""
    address: Optional[str] = ""
    tier: Literal["silver", "gold", "platinum"] = "silver"
    discount_pct: float = 0.0
    credit_limit: float = 0.0

class DistributorOut(DistributorIn):
    id: str
    created_at: str

class OrderItemIn(BaseModel):
    product_id: str
    quantity: int

class OrderIn(BaseModel):
    items: List[OrderItemIn]
    customer_name: str
    customer_email: EmailStr
    customer_phone: str
    shipping_address: str
    order_type: Literal["retail", "distributor"] = "retail"
    distributor_id: Optional[str] = None
    payment_method: Literal["cod", "prepaid"] = "cod"
    notes: Optional[str] = ""

class InvoiceIn(BaseModel):
    order_id: str
    is_interstate: bool = False

# ---- Auth Dependency ----
async def get_current_user(request: Request) -> dict:
    token = request.cookies.get("access_token")
    if not token:
        auth = request.headers.get("Authorization", "")
        if auth.startswith("Bearer "):
            token = auth[7:]
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")
    user = await db.users.find_one({"id": payload["sub"]}, {"_id": 0, "password_hash": 0})
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

def require_role(*roles: str):
    async def checker(user: dict = Depends(get_current_user)):
        if user.get("role") not in roles:
            raise HTTPException(status_code=403, detail="Forbidden")
        return user
    return checker

# ---- Auth Endpoints ----
@api.post("/auth/register")
async def register(inp: RegisterInput, response: Response):
    email = inp.email.lower()
    if await db.users.find_one({"email": email}):
        raise HTTPException(status_code=400, detail="Email already registered")
    role = inp.role if inp.role in ("customer", "distributor") else "customer"
    user_doc = {
        "id": str(uuid.uuid4()),
        "email": email,
        "password_hash": hash_password(inp.password),
        "name": inp.name,
        "role": role,
        "phone": inp.phone or "",
        "created_at": now_iso(),
    }
    await db.users.insert_one(user_doc)
    token = create_access_token(user_doc["id"], email, role)
    response.set_cookie("access_token", token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    user_doc.pop("password_hash", None)
    user_doc.pop("_id", None)
    return {"user": user_doc, "token": token}

@api.post("/auth/login")
async def login(inp: LoginInput, response: Response):
    email = inp.email.lower()
    user = await db.users.find_one({"email": email})
    if not user or not verify_password(inp.password, user["password_hash"]):
        raise HTTPException(status_code=401, detail="Invalid email or password")
    token = create_access_token(user["id"], email, user["role"])
    response.set_cookie("access_token", token, httponly=True, secure=False, samesite="lax", max_age=604800, path="/")
    user.pop("password_hash", None)
    user.pop("_id", None)
    return {"user": user, "token": token}

@api.post("/auth/logout")
async def logout(response: Response):
    response.delete_cookie("access_token", path="/")
    return {"ok": True}

@api.get("/auth/me")
async def me(user: dict = Depends(get_current_user)):
    return user

# ---- Products ----
@api.get("/products")
async def list_products(q: Optional[str] = None, category: Optional[str] = None, active_only: bool = False):
    query = {}
    if q:
        query["$or"] = [{"name": {"$regex": q, "$options": "i"}}, {"sku": {"$regex": q, "$options": "i"}}]
    if category:
        query["category"] = category
    if active_only:
        query["active"] = True
    docs = await db.products.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return docs

@api.get("/products/{pid}")
async def get_product(pid: str):
    doc = await db.products.find_one({"id": pid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Product not found")
    return doc

@api.post("/products")
async def create_product(inp: ProductIn, user: dict = Depends(require_role("admin", "staff"))):
    if await db.products.find_one({"sku": inp.sku}):
        raise HTTPException(400, "SKU already exists")
    doc = inp.model_dump()
    doc["id"] = str(uuid.uuid4())
    doc["created_at"] = now_iso()
    await db.products.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.put("/products/{pid}")
async def update_product(pid: str, inp: ProductIn, user: dict = Depends(require_role("admin", "staff"))):
    doc = await db.products.find_one({"id": pid})
    if not doc:
        raise HTTPException(404, "Product not found")
    updates = inp.model_dump()
    await db.products.update_one({"id": pid}, {"$set": updates})
    updated = await db.products.find_one({"id": pid}, {"_id": 0})
    return updated

@api.delete("/products/{pid}")
async def delete_product(pid: str, user: dict = Depends(require_role("admin"))):
    r = await db.products.delete_one({"id": pid})
    if r.deleted_count == 0:
        raise HTTPException(404, "Product not found")
    return {"ok": True}

@api.post("/products/{pid}/stock")
async def adjust_stock(pid: str, delta: int, user: dict = Depends(require_role("admin", "staff"))):
    doc = await db.products.find_one({"id": pid})
    if not doc:
        raise HTTPException(404, "Not found")
    new_stock = max(0, doc.get("stock", 0) + delta)
    await db.products.update_one({"id": pid}, {"$set": {"stock": new_stock}})
    return {"id": pid, "stock": new_stock}

# ---- Distributors ----
@api.get("/distributors")
async def list_distributors(user: dict = Depends(require_role("admin", "staff"))):
    return await db.distributors.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)

@api.post("/distributors")
async def create_distributor(inp: DistributorIn, user: dict = Depends(require_role("admin", "staff"))):
    if await db.distributors.find_one({"email": inp.email.lower()}):
        raise HTTPException(400, "Distributor email exists")
    doc = inp.model_dump()
    doc["email"] = doc["email"].lower()
    doc["id"] = str(uuid.uuid4())
    doc["created_at"] = now_iso()
    await db.distributors.insert_one(doc)
    doc.pop("_id", None)
    return doc

@api.put("/distributors/{did}")
async def update_distributor(did: str, inp: DistributorIn, user: dict = Depends(require_role("admin", "staff"))):
    r = await db.distributors.find_one({"id": did})
    if not r:
        raise HTTPException(404, "Not found")
    updates = inp.model_dump()
    updates["email"] = updates["email"].lower()
    await db.distributors.update_one({"id": did}, {"$set": updates})
    return await db.distributors.find_one({"id": did}, {"_id": 0})

@api.delete("/distributors/{did}")
async def delete_distributor(did: str, user: dict = Depends(require_role("admin"))):
    r = await db.distributors.delete_one({"id": did})
    if r.deleted_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True}

# ---- Orders ----
async def _build_order_from_input(inp: OrderIn) -> dict:
    items_out = []
    subtotal = 0.0
    discount_pct = 0.0
    if inp.order_type == "distributor" and inp.distributor_id:
        d = await db.distributors.find_one({"id": inp.distributor_id})
        if d:
            discount_pct = float(d.get("discount_pct", 0))
    for it in inp.items:
        p = await db.products.find_one({"id": it.product_id})
        if not p:
            raise HTTPException(400, f"Product {it.product_id} not found")
        unit_price = float(p.get("distributor_price") or p["price"]) if inp.order_type == "distributor" else float(p["price"])
        if discount_pct > 0:
            unit_price = round(unit_price * (1 - discount_pct / 100), 2)
        line_total = round(unit_price * it.quantity, 2)
        subtotal += line_total
        items_out.append({
            "product_id": p["id"],
            "sku": p["sku"],
            "name": p["name"],
            "quantity": it.quantity,
            "unit_price": unit_price,
            "gst_rate": float(p.get("gst_rate", 5.0)),
            "line_total": line_total,
        })
    # GST calc (aggregated later on invoice, but tracked here per item)
    gst_total = round(sum(i["line_total"] * i["gst_rate"] / 100 for i in items_out), 2)
    grand_total = round(subtotal + gst_total, 2)
    order = {
        "id": str(uuid.uuid4()),
        "order_number": f"KH-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "customer_name": inp.customer_name,
        "customer_email": inp.customer_email.lower(),
        "customer_phone": inp.customer_phone,
        "shipping_address": inp.shipping_address,
        "order_type": inp.order_type,
        "distributor_id": inp.distributor_id,
        "payment_method": inp.payment_method,
        "notes": inp.notes or "",
        "items": items_out,
        "subtotal": round(subtotal, 2),
        "gst_total": gst_total,
        "grand_total": grand_total,
        "status": "pending",
        "created_at": now_iso(),
    }
    return order

@api.post("/orders")
async def create_order(inp: OrderIn):
    order = await _build_order_from_input(inp)
    # decrement stock
    for it in order["items"]:
        p = await db.products.find_one({"id": it["product_id"]})
        if p and p.get("stock", 0) < it["quantity"]:
            raise HTTPException(400, f"Insufficient stock for {it['name']}")
    for it in order["items"]:
        await db.products.update_one({"id": it["product_id"]}, {"$inc": {"stock": -it["quantity"]}})
    await db.orders.insert_one(order)
    order.pop("_id", None)
    return order

@api.get("/orders")
async def list_orders(status: Optional[str] = None, user: dict = Depends(get_current_user)):
    query = {}
    if user["role"] not in ("admin", "staff"):
        query["customer_email"] = user["email"]
    if status:
        query["status"] = status
    docs = await db.orders.find(query, {"_id": 0}).sort("created_at", -1).to_list(500)
    return docs

@api.get("/orders/{oid}")
async def get_order(oid: str, user: dict = Depends(get_current_user)):
    doc = await db.orders.find_one({"id": oid}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Not found")
    if user["role"] not in ("admin", "staff") and doc["customer_email"] != user["email"]:
        raise HTTPException(403, "Forbidden")
    return doc

@api.put("/orders/{oid}/status")
async def update_order_status(oid: str, status: str, user: dict = Depends(require_role("admin", "staff"))):
    if status not in ("pending", "processing", "shipped", "delivered", "cancelled"):
        raise HTTPException(400, "Invalid status")
    r = await db.orders.update_one({"id": oid}, {"$set": {"status": status}})
    if r.matched_count == 0:
        raise HTTPException(404, "Not found")
    return {"ok": True, "status": status}

# ---- Invoices with GST ----
@api.post("/invoices")
async def create_invoice(inp: InvoiceIn, user: dict = Depends(require_role("admin", "staff"))):
    order = await db.orders.find_one({"id": inp.order_id}, {"_id": 0})
    if not order:
        raise HTTPException(404, "Order not found")
    existing = await db.invoices.find_one({"order_id": order["id"]}, {"_id": 0})
    if existing:
        return existing
    # Compute GST breakdown per item
    items = []
    cgst_total = sgst_total = igst_total = 0.0
    for it in order["items"]:
        tax = round(it["line_total"] * it["gst_rate"] / 100, 2)
        if inp.is_interstate:
            igst = tax
            cgst = sgst = 0.0
        else:
            cgst = round(tax / 2, 2)
            sgst = round(tax - cgst, 2)
            igst = 0.0
        cgst_total += cgst
        sgst_total += sgst
        igst_total += igst
        items.append({**it, "cgst": cgst, "sgst": sgst, "igst": igst, "tax_total": tax})
    invoice = {
        "id": str(uuid.uuid4()),
        "invoice_number": f"INV-{datetime.now().strftime('%y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
        "order_id": order["id"],
        "order_number": order["order_number"],
        "customer_name": order["customer_name"],
        "customer_email": order["customer_email"],
        "shipping_address": order["shipping_address"],
        "is_interstate": inp.is_interstate,
        "items": items,
        "subtotal": order["subtotal"],
        "cgst_total": round(cgst_total, 2),
        "sgst_total": round(sgst_total, 2),
        "igst_total": round(igst_total, 2),
        "grand_total": order["grand_total"],
        "created_at": now_iso(),
    }
    await db.invoices.insert_one(invoice)
    invoice.pop("_id", None)
    return invoice

@api.get("/invoices")
async def list_invoices(user: dict = Depends(require_role("admin", "staff"))):
    return await db.invoices.find({}, {"_id": 0}).sort("created_at", -1).to_list(500)

@api.get("/invoices/{iid}")
async def get_invoice(iid: str, user: dict = Depends(get_current_user)):
    inv = await db.invoices.find_one({"id": iid}, {"_id": 0})
    if not inv:
        raise HTTPException(404, "Not found")
    if user["role"] not in ("admin", "staff") and inv["customer_email"] != user["email"]:
        raise HTTPException(403, "Forbidden")
    return inv

# ---- Reports ----
@api.get("/reports/dashboard")
async def dashboard_stats(user: dict = Depends(require_role("admin", "staff"))):
    total_products = await db.products.count_documents({})
    active_products = await db.products.count_documents({"active": True})
    total_orders = await db.orders.count_documents({})
    pending_orders = await db.orders.count_documents({"status": "pending"})
    total_distributors = await db.distributors.count_documents({})
    low_stock = await db.products.find({"$expr": {"$lte": ["$stock", "$low_stock_threshold"]}}, {"_id": 0, "id": 1, "name": 1, "sku": 1, "stock": 1, "low_stock_threshold": 1}).to_list(20)
    # revenue
    pipeline = [{"$group": {"_id": None, "revenue": {"$sum": "$grand_total"}}}]
    rev = await db.orders.aggregate(pipeline).to_list(1)
    revenue = rev[0]["revenue"] if rev else 0
    # top products
    top_pipeline = [
        {"$unwind": "$items"},
        {"$group": {"_id": {"pid": "$items.product_id", "name": "$items.name"}, "qty": {"$sum": "$items.quantity"}, "sales": {"$sum": "$items.line_total"}}},
        {"$sort": {"qty": -1}},
        {"$limit": 5},
    ]
    top_products = await db.orders.aggregate(top_pipeline).to_list(5)
    top_products = [{"product_id": r["_id"]["pid"], "name": r["_id"]["name"], "qty": r["qty"], "sales": round(r["sales"], 2)} for r in top_products]
    # last 7 days sales
    seven_days_ago = (datetime.now(timezone.utc) - timedelta(days=6)).date().isoformat()
    sales_pipe = [
        {"$match": {"created_at": {"$gte": seven_days_ago}}},
        {"$group": {"_id": {"$substr": ["$created_at", 0, 10]}, "revenue": {"$sum": "$grand_total"}, "orders": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    daily = await db.orders.aggregate(sales_pipe).to_list(30)
    daily = [{"date": d["_id"], "revenue": round(d["revenue"], 2), "orders": d["orders"]} for d in daily]
    return {
        "total_products": total_products,
        "active_products": active_products,
        "total_orders": total_orders,
        "pending_orders": pending_orders,
        "total_distributors": total_distributors,
        "revenue": round(revenue, 2),
        "low_stock": low_stock,
        "top_products": top_products,
        "daily_sales": daily,
    }

@api.get("/reports/sales")
async def sales_report(days: int = 30, user: dict = Depends(require_role("admin", "staff"))):
    start = (datetime.now(timezone.utc) - timedelta(days=days)).date().isoformat()
    pipe = [
        {"$match": {"created_at": {"$gte": start}}},
        {"$group": {"_id": {"$substr": ["$created_at", 0, 10]}, "revenue": {"$sum": "$grand_total"}, "orders": {"$sum": 1}}},
        {"$sort": {"_id": 1}},
    ]
    rows = await db.orders.aggregate(pipe).to_list(365)
    return [{"date": r["_id"], "revenue": round(r["revenue"], 2), "orders": r["orders"]} for r in rows]

# ---- Categories ----
@api.get("/categories")
async def list_categories():
    cats = await db.products.distinct("category")
    return sorted([c for c in cats if c])

# ---- Health ----
@api.get("/")
async def root():
    return {"service": "Kaya's Herbals ERP", "status": "ok"}

# ---- Startup seed ----
async def seed():
    await db.users.create_index("email", unique=True)
    await db.products.create_index("sku", unique=True)
    admin = await db.users.find_one({"email": ADMIN_EMAIL.lower()})
    if not admin:
        await db.users.insert_one({
            "id": str(uuid.uuid4()),
            "email": ADMIN_EMAIL.lower(),
            "password_hash": hash_password(ADMIN_PASSWORD),
            "name": "Kaya Admin",
            "role": "admin",
            "phone": "",
            "created_at": now_iso(),
        })
        logger.info("Seeded admin user %s", ADMIN_EMAIL)
    elif not verify_password(ADMIN_PASSWORD, admin["password_hash"]):
        await db.users.update_one({"email": ADMIN_EMAIL.lower()}, {"$set": {"password_hash": hash_password(ADMIN_PASSWORD)}})
        logger.info("Rehashed admin password")
    # Seed sample products
    if await db.products.count_documents({}) == 0:
        samples = [
            {"name": "Ashwagandha Root Powder", "sku": "KH-ASH-001", "category": "Powders", "description": "Pure Ashwagandha root powder for stress relief and vitality. 100g pack.", "mrp": 599, "price": 499, "distributor_price": 349, "stock": 120, "gst_rate": 5, "image_url": "https://images.unsplash.com/photo-1607006344380-b6775a0824ab?w=800", "low_stock_threshold": 20, "active": True},
            {"name": "Neem Leaf Capsules", "sku": "KH-NEEM-002", "category": "Capsules", "description": "60 capsules of organic neem leaf extract. Supports skin & immunity.", "mrp": 449, "price": 379, "distributor_price": 269, "stock": 85, "gst_rate": 12, "image_url": "https://images.unsplash.com/photo-1584308972272-9e4e7685e80f?w=800", "low_stock_threshold": 15, "active": True},
            {"name": "Brahmi Herbal Tea", "sku": "KH-BRA-003", "category": "Teas", "description": "Loose leaf herbal tea infused with Brahmi. 100g.", "mrp": 349, "price": 299, "distributor_price": 210, "stock": 200, "gst_rate": 5, "image_url": "https://images.unsplash.com/photo-1597481499750-3e6b22637e12?w=800", "low_stock_threshold": 30, "active": True},
            {"name": "Turmeric Face Serum", "sku": "KH-TUR-004", "category": "Skincare", "description": "Cold-pressed turmeric serum with kumkumadi oil. 30ml glass bottle.", "mrp": 899, "price": 749, "distributor_price": 520, "stock": 45, "gst_rate": 18, "image_url": "https://images.unsplash.com/photo-1608571423902-eed4a5ad8108?w=800", "low_stock_threshold": 10, "active": True},
            {"name": "Triphala Detox Blend", "sku": "KH-TRI-005", "category": "Powders", "description": "Traditional three-fruit Ayurvedic blend for gentle detox. 150g.", "mrp": 399, "price": 329, "distributor_price": 230, "stock": 8, "gst_rate": 5, "image_url": "https://images.unsplash.com/photo-1518144328940-c9f6d19f42b9?w=800", "low_stock_threshold": 15, "active": True},
            {"name": "Rose & Sandalwood Ubtan", "sku": "KH-ROSE-006", "category": "Skincare", "description": "Natural bath ubtan with rose petals and sandalwood. 200g.", "mrp": 549, "price": 449, "distributor_price": 310, "stock": 60, "gst_rate": 18, "image_url": "https://images.unsplash.com/photo-1556228720-195a672e8a03?w=800", "low_stock_threshold": 12, "active": True},
        ]
        for s in samples:
            s["id"] = str(uuid.uuid4())
            s["created_at"] = now_iso()
        await db.products.insert_many(samples)
        logger.info("Seeded %d sample products", len(samples))

@app.on_event("startup")
async def _startup():
    try:
        await seed()
    except Exception as e:
        logger.exception("Seed failed: %s", e)

@app.on_event("shutdown")
async def _shutdown():
    client.close()

app.include_router(api)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)
