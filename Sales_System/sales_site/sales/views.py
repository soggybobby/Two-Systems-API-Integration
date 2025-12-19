from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from django.conf import settings
import requests

from .models import Customer, Sale, Product
from .serializers import CustomerSerializer, SaleSerializer


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("name")
    serializer_class = CustomerSerializer


class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all().order_by("-created_at")
    serializer_class = SaleSerializer


@api_view(["GET"])
def product_list(request):
    """
    JSON list for shop + (optional) unified frontend.
    Only show active AND published products.
    Uses effective_price for sale override.
    """
    products = Product.objects.filter(is_active=True, published_to_shop=True).order_by("name")
    data = [
        {
            "sku": p.sku,
            "name": p.name,
            "unit": p.unit,
            "price": float(p.effective_price),
            "stock_qty": int(p.stock_qty),
        }
        for p in products
    ]
    return Response(data)


@api_view(["POST"])
def checkout(request):
    """
    Creates the Sale in Django, then deducts stock in Inventory_System via:
      POST {INVENTORY_API_BASE}/stock/adjust
    """
    payload = {
        "customer": request.data.get("customer"),
        "status": "NEW",
        "items": request.data.get("items", []),
    }

    ser = SaleSerializer(data=payload)
    ser.is_valid(raise_exception=True)
    sale = ser.save()

    # Build the inventory adjustment payload from request items
    # Expected request item shape:
    # {"sku":"ABC-01","qty":2,...}
    items = []
    for it in payload["items"]:
        sku = str(it.get("sku", "")).strip().upper()
        qty = int(it.get("qty") or 0)
        if sku and qty > 0:
            items.append({"sku": sku, "qty": qty})

    # If there are items, notify Inventory_System to deduct qty
    if items:
        base = getattr(settings, "INVENTORY_API_BASE", "http://127.0.0.1:3001")
        url = f"{base}/stock/adjust"

        # Use sale_no if you have it, else fallback to sale.id
        ref_id = getattr(sale, "sale_no", None) or str(sale.id)

        inv_payload = {
            "refType": "SALE",
            "refId": ref_id,
            "items": items,
        }

        try:
            resp = requests.post(url, json=inv_payload, timeout=10)
            resp.raise_for_status()
        except Exception as e:
            # Sale is already created, but inventory failed.
            # Return a clear error so you can see it on the frontend.
            return Response(
                {
                    "error": "Sale created, but failed to deduct inventory",
                    "sale": SaleSerializer(sale).data,
                    "inventory_url": url,
                    "inventory_payload": inv_payload,
                    "details": str(e),
                },
                status=502,
            )

    return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
