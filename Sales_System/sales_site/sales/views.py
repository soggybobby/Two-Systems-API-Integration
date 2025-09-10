from rest_framework import viewsets, status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from .models import Customer, Sale
from .serializers import CustomerSerializer, SaleSerializer

# Temporary in-memory catalog (replace with Inventory later)
PRODUCTS = [
    {"sku":"KB-001","name":"Mechanical Keyboard 87-key","unit":"pcs","price":1999.00},
    {"sku":"MS-010","name":"Wireless Mouse","unit":"pcs","price":599.00},
    {"sku":"PAD-003","name":"Large Desk Mat","unit":"pcs","price":399.00},
]

class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all().order_by("name")
    serializer_class = CustomerSerializer

class SaleViewSet(viewsets.ModelViewSet):
    queryset = Sale.objects.all().order_by("-created_at")
    serializer_class = SaleSerializer

@api_view(["GET"])
def product_list(request):
    return Response(PRODUCTS)

@api_view(["POST"])
def checkout(request):
    """
    body:
    {
      "customer": <customer_id>,
      "items": [
        {"sku":"KB-001","product_name":"Mechanical Keyboard 87-key","unit":"pcs","qty":1,"unit_price":1999.00}
      ]
    }
    """
    payload = {
        "customer": request.data.get("customer"),
        "status": "NEW",
        "items": request.data.get("items", [])
    }
    ser = SaleSerializer(data=payload)
    ser.is_valid(raise_exception=True)
    sale = ser.save()
    return Response(SaleSerializer(sale).data, status=status.HTTP_201_CREATED)
