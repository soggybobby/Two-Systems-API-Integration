# sales/api_products.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Product


@api_view(["GET"])
@permission_classes([AllowAny])
def list_products(request):
    """
    Public API used by:
      - Inventory_System (Node) -> /products/sync
      - unified-frontend React dashboard

    Returns active products with stock_qty included.
    """
    qs = Product.objects.filter(is_active=True).order_by("sku")

    data = []
    for p in qs:
        data.append({
            "sku": p.sku,
            "name": p.name,
            "description": p.description,
            "unit": p.unit,
            # send as string to be safe with Decimal
            "price": str(p.price),
            "stock_qty": p.stock_qty,
        })

    return Response(data)
