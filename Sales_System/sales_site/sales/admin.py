from django.contrib import admin
from .models import Customer, Sale, SaleItem

class SaleItemInline(admin.TabularInline):
    model = SaleItem
    extra = 0

@admin.register(Sale)
class SaleAdmin(admin.ModelAdmin):
    list_display = ("sale_no", "customer", "status", "total_amount", "created_at", "paid_at")
    list_filter = ("status",)
    inlines = [SaleItemInline]

admin.site.register(Customer)
