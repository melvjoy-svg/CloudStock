from django.urls import path
from . import views

urlpatterns = [
    path('', views.supplier_list, name='supplier_list'),
    path('add/', views.supplier_add, name='supplier_add'),
    path('edit/<int:id>/', views.supplier_edit, name='supplier_edit'),
    path('delete/<int:id>/', views.supplier_delete, name='supplier_delete'),
]