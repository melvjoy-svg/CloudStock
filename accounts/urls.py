from django.urls import path
from .views import user_list, user_add, owner_register, staff_list, staff_add, staff_edit

urlpatterns = [
    path('register/', owner_register, name='owner_register'),
    path('staff/', staff_list, name='staff_list'),
    path('staff/add/', staff_add, name='staff_add'),
    path('staff/<int:id>/edit/', staff_edit, name='staff_edit'),
    path('', user_list, name='user_list'),
    path('add/', user_add, name='user_add'),
]
