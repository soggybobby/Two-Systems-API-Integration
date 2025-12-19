from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product

@api_view(["POST"])
@permission_classes([AllowAny])
def inventory_event(request):
    """
    Inventory -> Sales event payload (single product):
    {
      "sku": "ABC-01",
      "name": "Mouse",
      "description": "",
      "unit": "pcs",
      "listPrice": 100,
      "publishedToShop": true,
      "salePriceOverride": null,
      "status": "ACTIVE",
      "currentQty": 198
    }
    """
    data = request.data
    sku = str(data.get("sku", "")).strip().upper()
    if not sku:
      return Response({"error": "sku is required"}, status=400)

    # upsert into Sales DB
    p, created = Product.objects.update_or_create(
        sku=sku,
        defaults={
            "name": data.get("name", ""),
            "unit": data.get("unit") or "pcs",
            "price": data.get("listPrice") or 0,          # map Inventory listPrice -> Sales price
            "stock_qty": data.get("currentQty") or 0,     # map Inventory currentQty -> Sales stock_qty
            "published_to_shop": bool(data.get("publishedToShop", False)),
            "sale_price_override": data.get("salePriceOverride"),
            "is_active": (data.get("status", "ACTIVE") == "ACTIVE"),
        }
    )

    return Response({"ok": True, "created": created, "sku": sku})
