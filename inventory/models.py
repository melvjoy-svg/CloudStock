from django.db import models
from tenants.models import Tenant
from products.models import Product


class Inventory(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='inventory'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='inventory_records'
    )
    quantity = models.PositiveIntegerField(default=0)
    last_updated = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'product'],
                name='unique_inventory_per_tenant_product'
            )
        ]
        ordering = ['product__name']

    def __str__(self):
        return f"{self.product} - {self.quantity}"


class StockTransaction(models.Model):
    TRANSACTION_TYPES = [
        ('PURCHASE', 'Purchase'),
        ('SALE', 'Sale'),
        ('RETURN', 'Return'),
        ('ADJUSTMENT', 'Adjustment'),
    ]

    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='stock_transactions'
    )
    product = models.ForeignKey(
        Product, on_delete=models.CASCADE, related_name='stock_transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    quantity = models.PositiveIntegerField()
    transaction_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-transaction_date', '-id']

    def __str__(self):
        return f"{self.product} - {self.transaction_type} - {self.quantity}"
