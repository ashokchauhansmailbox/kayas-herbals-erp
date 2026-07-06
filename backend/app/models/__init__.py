"""Explicit re-exports so Alembic autogenerate sees every mapped class.

Any new model file MUST be imported here or Alembic will not detect it.
"""

from app.db.base import Base  # noqa: F401
from app.models import (  # noqa: F401
    catalog,
    customer,
    distributor,
    identity,
    inventory,
    master_data,
    purchase,
)
from app.models.catalog import (  # noqa: F401
    Certification,
    Product,
    ProductDocument,
    ProductImage,
    ProductPriceHistory,
    ProductVariant,
    PurchasePriceHistory,
)
from app.models.customer import (  # noqa: F401
    Address,
    CustomerProfile,
    Referral,
    Wallet,
    WalletTransaction,
)
from app.models.distributor import (  # noqa: F401
    Distributor,
    DistributorTier,
    KycDocument,
    PriceList,
    PriceListItem,
)
from app.models.identity import (  # noqa: F401
    ActivityLog,
    AuditLog,
    Permission,
    Role,
    RolePermission,
    Session,
    User,
    UserInvitation,
    UserRole,
)
from app.models.inventory import (  # noqa: F401
    Batch,
    StockAdjustment,
    StockAlert,
    StockLedger,
    StockSnapshot,
    StockTransfer,
    StockTransferItem,
)
from app.models.master_data import (  # noqa: F401
    Brand,
    Category,
    CourierPartner,
    GstRate,
    HsnCode,
    PaymentTerm,
    TaxRule,
    Transporter,
    Unit,
    Warehouse,
)
from app.models.purchase import (  # noqa: F401
    GRN,
    GRNItem,
    PurchaseOrder,
    PurchaseOrderItem,
    Vendor,
    VendorInvoice,
)

__all__ = [
    "Base",
    # identity
    "User",
    "Role",
    "Permission",
    "RolePermission",
    "UserRole",
    "Session",
    "UserInvitation",
    "AuditLog",
    "ActivityLog",
    # master_data
    "Unit",
    "GstRate",
    "HsnCode",
    "Category",
    "Brand",
    "Warehouse",
    "PaymentTerm",
    "TaxRule",
    "Transporter",
    "CourierPartner",
    # catalog
    "Product",
    "ProductVariant",
    "ProductImage",
    "ProductDocument",
    "Certification",
    "ProductPriceHistory",
    "PurchasePriceHistory",
    # inventory
    "Batch",
    "StockAdjustment",
    "StockTransfer",
    "StockTransferItem",
    "StockLedger",
    "StockSnapshot",
    "StockAlert",
    # purchase
    "Vendor",
    "PurchaseOrder",
    "PurchaseOrderItem",
    "GRN",
    "GRNItem",
    "VendorInvoice",
    # distributor
    "DistributorTier",
    "Distributor",
    "PriceList",
    "PriceListItem",
    "KycDocument",
    # customer
    "CustomerProfile",
    "Address",
    "Wallet",
    "WalletTransaction",
    "Referral",
]
