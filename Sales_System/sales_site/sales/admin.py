from django.contrib import admin
from .models import Customer, Sale, SaleItem, Product

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("sale_no", "customer", "status", "total_amount", "created_at", "paid_at")
    list_filter = ("status",)
    inlines = [SaleItemInline]

admin.site.register(Customer)

@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = (
        "sku",
        "name",
        "unit",
        "price",
        "sale_price_override",
        "effective_price",
        "stock_qty",
        "published_to_shop",
        "is_active",
        "updated_at",
    )
    list_filter = ("published_to_shop", "is_active")
    search_fields = ("sku", "name")
