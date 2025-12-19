from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from decimal import Decimal, InvalidOperation

from .models import Product


def to_decimal(v, default="0"):
    try:
        if v is None or v == "":
            return Decimal(default)
        return Decimal(str(v))
    except (InvalidOperation, TypeError):
        return Decimal(default)


@api_view(["POST"])
@permission_classes([AllowAny])
def inventory_product_upsert(request):
    """
    Receives Inventory outbox events like:
    {
      "type": "PRODUCT_UPSERT",
      "product": {
        "sku": "...",
        "name": "...",
        "unit": "...",
        "listPrice": "10.00",
        "currentQty": 5,
        "publishedToShop": true,
        "salePriceOverride": "9.50"
      }
    }
    """
    data = request.data or {}
    product = data.get("product") or {}

    sku = str(product.get("sku", "")).strip().upper()
    if not sku:
        return Response({"error": "Missing sku"}, status=400)

    defaults = {}

    if "name" in product:
        defaults["name"] = product.get("name") or ""
    if "unit" in product:
        defaults["unit"] = product.get("unit") or "pcs"

    # Sales model uses price, inventory uses listPrice
    if "listPrice" in product:
        defaults["price"] = to_decimal(product.get("listPrice"), "0")

    if "currentQty" in product:
        try:
            defaults["stock_qty"] = int(product.get("currentQty") or 0)
        except Exception:
            defaults["stock_qty"] = 0

    # Optional fields, only set if your Sales Product model has them
    # published_to_shop
    if hasattr(Product, "published_to_shop") and "publishedToShop" in product:
        defaults["published_to_shop"] = bool(product.get("publishedToShop"))

    # sale_price_override
    if hasattr(Product, "sale_price_override") and "salePriceOverride" in product:
        v = product.get("salePriceOverride")
        defaults["sale_price_override"] = to_decimal(v, "0") if v not in (None, "") else None

    obj, created = Product.objects.update_or_create(sku=sku, defaults=defaults)

    return Response({
        "ok": True,
        "created": created,
        "sku": obj.sku,
        "updated_fields": list(defaults.keys()),
    })
