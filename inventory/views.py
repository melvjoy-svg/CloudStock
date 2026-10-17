from django.shortcuts import render

from .models import Inventory, StockTransaction
from accounts.decorators import role_required


# =========================
# INVENTORY
# =========================

@role_required('SUPER_ADMIN', 'BUSINESS_OWNER', 'STAFF')
def inventory_list(request):

    if request.user.role == 'SUPER_ADMIN':

        inventories = Inventory.objects.select_related(
            'tenant',
            'product'
        ).all().order_by(
            'product__name'
        )

    else:

        inventories = Inventory.objects.select_related(
            'tenant',
            'product'
        ).filter(
            tenant=request.user.tenant
        ).order_by(
            'product__name'
        )

    return render(
        request,
        'inventory/inventory_list.html',
        {
            'inventories': inventories
        }
    )


# =========================
# STOCK TRANSACTIONS
# =========================

@role_required('SUPER_ADMIN', 'BUSINESS_OWNER', 'STAFF')
def stock_transactions(request):

    if request.user.role == 'SUPER_ADMIN':

        transactions = StockTransaction.objects.select_related(
            'tenant',
            'product'
        ).all().order_by(
            '-transaction_date'
        )

    else:

        transactions = StockTransaction.objects.select_related(
            'tenant',
            'product'
        ).filter(
            tenant=request.user.tenant
        ).order_by(
            '-transaction_date'
        )

    return render(
        request,
        'inventory/stock_transactions.html',
        {
            'transactions': transactions
        }
    )