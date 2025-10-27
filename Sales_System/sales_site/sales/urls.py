# sales/urls.py
from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from sales.views import (
    CustomerViewSet,
    SaleViewSet,
    product_list,   # JSON product list (legacy/plain)
    checkout,       # JSON checkout (legacy/plain)
)
from sales.store_views import (
    shop_home,          # HTML
    add_to_cart,        # HTML
    view_cart,          # HTML
    update_cart,        # HTML
    checkout_form,      # HTML
    place_order,        # HTML
    remove_from_cart,   # HTML
)
from sales.api import ProductViewSet
from .views_inventory_sync import pull_from_inventory, push_to_inventory  # correct names

router = DefaultRouter()
router.register(r"customers", CustomerViewSet)
router.register(r"sales",     SaleViewSet)
router.register(r"products",  ProductViewSet)

urlpatterns = [
    # Admin
    # If admin is already in sales_site/sales_site/urls.py, comment this to avoid duplicate namespace warnings.
    path("admin/", admin.site.urls),

    # Home
    path("", shop_home, name="home"),
    path("shop/", shop_home, name="shop_home"),

    # Storefront (HTML)
    path("cart/",           view_cart,        name="view_cart"),
    path("cart/update/",    update_cart,      name="update_cart"),
    path("cart/remove/",    remove_from_cart, name="remove_from_cart"),
    path("add/",            add_to_cart,      name="add_to_cart"),
    path("checkout/",       checkout_form,    name="checkout_form"),
    path("place-order/",    place_order,      name="place_order"),

    # JSON endpoints (legacy/plain)
    path("products/",        product_list, name="product_list_json"),
    path("shop/products/",   product_list, name="product_list_json_shop"),  # for your Node caller
    path("checkout-json/",   checkout,     name="checkout_json"),

    # REST API
    path("api/", include(router.urls)),

    # Inventory ↔ Sales sync
    path("api/sync-from-inventory/", pull_from_inventory, name="sync_from_inventory"),  # GET
    path("api/sync-to-inventory/",   push_to_inventory,  name="sync_to_inventory"),    # POST
]
