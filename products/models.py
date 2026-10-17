from django.db import models
from django.db.models import Q
from tenants.models import Tenant


class Category(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='categories'
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'name'],
                name='unique_category_per_tenant'
            )
        ]
        ordering = ['name']

    def __str__(self):
        return self.name


class Product(models.Model):
    tenant = models.ForeignKey(
        Tenant, on_delete=models.CASCADE, related_name='products'
    )
    category = models.ForeignKey(
        Category, on_delete=models.PROTECT,
        related_name='products', null=True, blank=True
    )
    name = models.CharField(max_length=200)
    sku = models.CharField(max_length=50)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    cost_price = models.DecimalField(max_digits=10, decimal_places=2)
    stock_quantity = models.PositiveIntegerField(default=0)
    reorder_level = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['tenant', 'sku'],
                name='unique_product_sku_per_tenant'
            ),
            models.CheckConstraint(
                condition=Q(price__gte=0),
                name='product_price_non_negative'
            ),
            models.CheckConstraint(
                condition=Q(cost_price__gte=0),
                name='product_cost_non_negative'
            ),
        ]
        ordering = ['name']

    def __str__(self):
        return self.name
