from django.urls import path
from .views import sale_list, sale_add, sale_detail, invoice_view
urlpatterns=[
    path('',sale_list,name='sale_list'),
    path('add/',sale_add,name='sale_add'),
    path('<int:id>/',sale_detail,name='sale_detail'),
    path('<int:id>/invoice/',invoice_view,name='invoice_view'),
]
