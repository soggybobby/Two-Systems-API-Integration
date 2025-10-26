from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from sales.views import (
    CustomerViewSet,
    SaleViewSet,
    product_list,
    checkout,
)
from sales.store_views import (
    shop_home,
    add_to_cart,
    view_cart,
    update_cart,
    checkout_form,
    place_order,
    remove_from_cart,
)
from sales.api import ProductViewSet  # make sure this exists

# --- REST API router ---
router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"sales", SaleViewSet)
router.register(r"products", ProductViewSet)

urlpatterns = [
    # --- Admin site ---
    path("admin/", admin.site.urls),

    # --- Home redirect (optional simple fix for /) ---
    path("", shop_home, name="home"),  # now http://127.0.0.1:5000/ will show shop_home

    # --- Storefront (HTML) routes ---
    path("", shop_home, name="shop_home"),
    path("cart/", view_cart, name="view_cart"),
    path("cart/update/", update_cart, name="update_cart"),
    path("cart/remove/", remove_from_cart, name="remove_from_cart"),
    path("add/", add_to_cart, name="add_to_cart"),
    path("checkout/", checkout_form, name="checkout_form"),
    path("place-order/", place_order, name="place_order"),

    # --- Legacy endpoints ---
    path("products/", product_list),
    path("checkout/", checkout),

    # --- REST API routes ---
    path("api/", include(router.urls)),  # /api/products/, /api/sales/, /api/customers/
]
