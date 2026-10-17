from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import User

@admin.register(User)
class CloudStockUserAdmin(UserAdmin):
    fieldsets = UserAdmin.fieldsets + (('CloudStock', {'fields': ('role', 'tenant')}),)
    add_fieldsets = UserAdmin.add_fieldsets + (('CloudStock', {'fields': ('role', 'tenant')}),)
