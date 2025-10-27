import requests
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.conf import settings

from .models import Product
from .api_inventory import fetch_inventory_products, upsert_into_sales

@api_view(["GET"])
@permission_classes([AllowAny])
def pull_from_inventory(request):
    """
    Inventory → Sales: pull all products from Inventory_System and upsert into Django.
    Returns detailed diagnostics so we can see any skips.
    """
    try:
        items = fetch_inventory_products()
        upsert_result = upsert_into_sales(items)
        return Response({
            "message": "Synced Inventory → Sales",
            **upsert_result,
            "sample": items[:3],  # tiny peek
        })
    except Exception as e:
        return Response({"error": str(e)}, status=500)

@api_view(["POST"])
@permission_classes([AllowAny])
def push_to_inventory(request):
    """
    Sales → Inventory: push all Django products into Inventory_System.
    """
    try:
        products = list(
            Product.objects.values(
                "sku", "name", "description", "unit", "price", "stock_qty"
            )
        )
        # Transform for Inventory payload
        payload = []
        for p in products:
            payload.append({
                "sku": str(p["sku"]).strip().upper(),
                "name": p["name"],
                "description": p.get("description") or "",
                "unit": p.get("unit") or "pcs",
                "listPrice": str(p["price"]),   # send as string to avoid float issues
                "status": "ACTIVE",
                "currentQty": int(p.get("stock_qty") or 0),
            })

        base = getattr(settings, "INVENTORY_API_BASE", "http://127.0.0.1:3001")
        url = f"{base}/products/sync-from-sales"
        resp = requests.post(url, json=payload, timeout=10)

        if resp.status_code == 200:
            return Response({
                "message": "Pushed Sales → Inventory",
                "count": len(payload),
                "inventory_response": resp.json(),
            })
        return Response({"status": resp.status_code, "body": resp.text}, status=500)
    except Exception as e:
        return Response({"error": str(e)}, status=500)
