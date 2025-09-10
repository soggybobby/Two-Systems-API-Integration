from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SaleViewSet, product_list, checkout

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"sales",     SaleViewSet)

urlpatterns = [
    path("shop/products/", product_list),
    path("shop/checkout/", checkout),
    path("", include(router.urls)),
]
