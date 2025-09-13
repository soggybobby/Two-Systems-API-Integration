from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CustomerViewSet, SaleViewSet, product_list, checkout
from .store_views import shop_home, add_to_cart, view_cart, update_cart, checkout_form, place_order, remove_from_cart

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"sales",     SaleViewSet)

urlpatterns = [
    # Storefront
    path("shop/", shop_home, name="shop_home"),
    path("shop/cart/", view_cart, name="view_cart"),
    path("shop/cart/update/", update_cart, name="update_cart"),
    path("shop/cart/remove/", remove_from_cart, name="remove_from_cart"),
    path("shop/add/", add_to_cart, name="add_to_cart"),
    path("shop/checkout/", checkout_form, name="checkout_form"),
    path("shop/place-order/", place_order, name="place_order"),

    # API
    path("shop/products/", product_list),
    path("shop/checkout/", checkout),
    path("", include(router.urls)),
]
