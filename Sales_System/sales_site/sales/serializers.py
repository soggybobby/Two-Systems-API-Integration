from rest_framework import serializers
from .models import Customer, Sale, SaleItem

class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"

class SaleItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = SaleItem
        exclude = ("sale_item_id",)

class SaleSerializer(serializers.ModelSerializer):
    items = SaleItemSerializer(many=True)

    class Meta:
        model = Sale
        fields = ("sale_id","sale_no","customer","status","total_amount","created_at","paid_at","items")
        read_only_fields = ("sale_no","total_amount","created_at","paid_at")

    def create(self, validated_data):
        items_data = validated_data.pop("items", [])
        sale = Sale.objects.create(**validated_data)
        for item in items_data:
            SaleItem.objects.create(sale=sale, **item)
        sale.save()  # recompute total
        return sale
