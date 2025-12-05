# sales/views.py
from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response

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
    JSON product list used by:
      - Node Inventory_System (/shop/products/)
      - unified-frontend React dashboard (Load Sales products)

    We return:
        sku, name, description (if any), unit, price (float), stock_qty
    """
    qs = Product.objects.filter(is_active=True).order_by("name")

    data = []
    for p in qs:
        data.append({
            "sku": p.sku,
            "name": p.name,
            # use getattr so it won't crash if 'description' field doesn't exist
            "description": getattr(p, "description", ""),
            "unit": p.unit,
            # keep as float so frontend stays the same as before
            "price": float(p.price),
            "stock_qty": p.stock_qty,
        })

    return Response(data)


@api_view(["POST"])
def checkout(request):
    """
    body:
    {
      "customer": <customer_id>,
      "items": [
        {
          "sku": "KB-001",
          "product_name": "Mechanical Keyboard 87-key",
          "unit": "pcs",
          "qty": 1,
          "unit_price": 1999.00
        }
      ]
    }
    """
    payload = {
        "customer": request.data.get("customer"),
        "status": "NEW",
        "items": request.data.get("items", []),
    }
    ser = SaleSerializer(data=payload)
    ser.is_valid(raise_exception=True)
    sale = ser.save()
    return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)