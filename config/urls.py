"""
URL configuration for config project.

The `urlpatterns` list routes URLs to views.
"""

from django.contrib import admin
from django.urls import path, include

from accounts.views import (
    home_view,
    login_view,
    logout_view,
    dashboard_view,
)


urlpatterns = [

    path('admin/', admin.site.urls),

    # CloudStock Landing Page
    path('', home_view, name='home'),

    # Authentication
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),

    # Dashboard
    path('dashboard/', dashboard_view, name='dashboard'),

    # CloudStock Modules
    path('tenants/', include('tenants.urls')),
    path('accounts/', include('accounts.urls')),
    path('products/', include('products.urls')),
    path('suppliers/', include('suppliers.urls')),
    path('purchases/', include('purchases.urls')),
    path('inventory/', include('inventory.urls')),
    path('customers/', include('customers.urls')),
    path('sales/', include('sales.urls')),
    path('reports/', include('reports.urls')),
]