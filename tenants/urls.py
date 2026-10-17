from django.urls import path
from .views import tenant_list, tenant_add, tenant_edit, tenant_delete

urlpatterns = [
    path('', tenant_list, name='tenant_list'),
    path('add/', tenant_add, name='tenant_add'),
    path('edit/<int:id>/', tenant_edit, name='tenant_edit'),
    path('delete/<int:id>/', tenant_delete, name='tenant_delete'),
]