from django.contrib import admin
from .models import Customer, Sale, SaleItem, Product


# ------------------------
# Sale Item Inline
# ------------------------
class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0


# ------------------------
# Sale Admin
# ------------------------
@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = (
        "sale_no",
        "customer",
        "status",
        "total_amount",
        "created_at",
        "paid_at",
    )
    list_filter = ("status",)
    inlines = [SaleItemInline]


# ------------------------
# Customer Admin
# ------------------------
admin.site.register(Customer)


# ------------------------
# Product Admin (UPDATED)
# ------------------------
@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "unit",
        "price",
        "stock_qty",   # <-- added for inventory sync
        "is_active",
        "updated_at",
    )
    list_editable = (
        "price",
        "stock_qty",   # <-- editable in admin
        "is_active",
    )
    list_filter = ("is_active",)
    search_fields = ("sku", "name")
