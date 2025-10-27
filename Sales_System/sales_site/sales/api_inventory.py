import requests
from decimal import Decimal, InvalidOperation
from django.conf import settings
from django.db import transaction
from .models import Product

def _headers():
    h = {}
    if getattr(settings, "INVENTORY_API_KEY", ""):
        h["Authorization"] = f"Bearer {settings.INVENTORY_API_KEY}"
    return h

def fetch_inventory_products():
    """
    Calls Inventory_System GET /products
    Expected fields per product: sku, name, description?, unit, listPrice, status, currentQty
    """
    base = getattr(settings, "INVENTORY_API_BASE", "http://127.0.0.1:3001")
    url = f"{base}/products"
    r = requests.get(url, headers=_headers(), timeout=10)
    r.raise_for_status()
    return r.json()

def _to_decimal(val, default="0"):
    if val is None or val == "":
        val = default
    try:
        # Accept numbers or numeric strings
        return Decimal(str(val))
    except (InvalidOperation, TypeError):
        return Decimal(default)

@transaction.atomic
def upsert_into_sales(products):
    """
    Inventory -> Sales field mapping:
      listPrice -> price (Decimal)
      currentQty -> stock_qty (int)
      status == 'ACTIVE' -> is_active True else False
    Returns a rich result for diagnostics.
    """
    result = {
        "received": len(products),
        "created": [],
        "updated": [],
        "skipped": [],   # [{sku, reason}]
        "errors": []     # [{sku, error}]
    }

    for p in products:
        try:
            raw_sku = p.get("sku")
            if not raw_sku:
                result["skipped"].append({"sku": None, "reason": "missing sku"})
                continue

            sku = str(raw_sku).strip().upper()
            name = (p.get("name") or "").strip()
            unit = (p.get("unit") or "pcs").strip() or "pcs"
            price = _to_decimal(p.get("listPrice"))
            stock_qty = int(p.get("currentQty") or 0)
            is_active = (str(p.get("status") or "ACTIVE").upper() == "ACTIVE")

            # Basic validation
            if not name:
                result["skipped"].append({"sku": sku, "reason": "empty name"})
                continue

            obj, created = Product.objects.update_or_create(
                sku=sku,
                defaults={
                    "name": name,
                    "unit": unit,
                    "price": price,
                    "stock_qty": stock_qty,
                    "is_active": is_active,
                },
            )
            (result["created"] if created else result["updated"]).append(sku)

        except Exception as e:
            result["errors"].append({"sku": p.get("sku"), "error": str(e)})

    return result
