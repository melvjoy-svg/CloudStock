from django.db import models
from django.contrib.auth.models import AbstractUser
from tenants.models import Tenant


class User(AbstractUser):
    ROLE_CHOICES = [
        ('SUPER_ADMIN', 'Super Admin'),
        ('BUSINESS_OWNER', 'Business Owner'),
        ('STAFF', 'Staff'),
    ]

    tenant = models.ForeignKey(Tenant, on_delete=models.CASCADE, null=True, blank=True, related_name='users')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='STAFF')

    # Fine-grained permissions for staff accounts. Owners and super admins bypass these flags.
    can_manage_products = models.BooleanField(default=False)
    can_manage_purchases = models.BooleanField(default=False)
    can_manage_sales = models.BooleanField(default=True)
    can_manage_customers = models.BooleanField(default=True)
    can_view_reports = models.BooleanField(default=False)

    def __str__(self):
        return self.username
