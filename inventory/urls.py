from django.urls import path
from . import views


urlpatterns = [
    path('', views.inventory_list, name='inventory_list'),
    path(
        'transactions/',
        views.stock_transactions,
        name='stock_transactions'
    ),
]