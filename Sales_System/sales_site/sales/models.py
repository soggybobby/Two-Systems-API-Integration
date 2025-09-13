from django.db import models
from django.utils import timezone
from django.core.validators import MinValueValidator
import uuid

class Customer(models.Model):
    customer_id = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return f"{self.name} ({self.email})"


class Sale(models.Model):
    class Status(models.TextChoices):
        NEW = "NEW", "New"
        PAID = "PAID", "Paid"
        CANCELLED = "CANCELLED", "Cancelled"

    sale_id = models.AutoField(primary_key=True)
    sale_no = models.CharField(max_length=24, unique=True, editable=False)
    customer = models.ForeignKey(Customer, on_delete=models.PROTECT, related_name="sales")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.NEW)
    total_amount = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(default=timezone.now, editable=False)
    paid_at = models.DateTimeField(null=True, blank=True)

    def save(self, *args, **kwargs):
        if not self.sale_no:
            # Simple unique sale number like 2025-xxxxx
            self.sale_no = timezone.now().strftime("%Y%m%d") + "-" + str(uuid.uuid4().hex[:6]).upper()
        super().save(*args, **kwargs)
        # Recompute after items exist
        total = sum(item.line_total for item in self.items.all())
        if self.total_amount != total:
            self.total_amount = total
            super().save(update_fields=["total_amount"])

    def __str__(self):
        return self.sale_no


class SaleItem(models.Model):
    sale_item_id = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sale, on_delete=models.CASCADE, related_name="items")
    sku = models.CharField(max_length=64)
    product_name = models.CharField(max_length=200)
    unit = models.CharField(max_length=30)
    qty = models.PositiveIntegerField(validators=[MinValueValidator(1)])
    unit_price = models.DecimalField(max_digits=12, decimal_places=2)
    line_total = models.DecimalField(max_digits=12, decimal_places=2, editable=False)

    def save(self, *args, **kwargs):
        self.line_total = self.qty * self.unit_price
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.product_name} x{self.qty}"
    
class Product(models.Model):
    sku = models.CharField(max_length=64, unique=True)
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=30, default="pcs")
    price = models.DecimalField(max_digits=12, decimal_places=2)
    stock_qty = models.PositiveIntegerField(default=0)   # <--- NEW
    is_active = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.sku} – {self.name}"

