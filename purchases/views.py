from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Purchase, PurchaseItem
from tenants.models import Tenant
from suppliers.models import Supplier
from products.models import Product
from inventory.models import Inventory, StockTransaction
from accounts.decorators import staff_permission_required


def _tenant_options(request):
    return Tenant.objects.filter(is_active=True, id=request.user.tenant_id).order_by('name') if request.user.role != 'SUPER_ADMIN' else Tenant.objects.filter(is_active=True).order_by('name')


def _rows(post, price_key):
    ids = post.getlist('product_ids')
    qtys = post.getlist('quantities')
    prices = post.getlist(price_key)
    # Backward compatibility with the original single-item form.
    if not ids and post.get('product'): ids = [post.get('product')]
    if not qtys and post.get('quantity'): qtys = [post.get('quantity')]
    if not prices and post.get(price_key.replace('s', '')): prices = [post.get(price_key.replace('s', ''))]
    rows = []
    for i, pid in enumerate(ids):
        if not pid: continue
        try:
            qty = int(qtys[i]); price = Decimal(prices[i])
            if qty <= 0 or price < 0: raise ValueError
        except (IndexError, TypeError, ValueError, InvalidOperation):
            raise ValueError('Every item must have a valid positive quantity and non-negative price.')
        rows.append((int(pid), qty, price))
    if not rows: raise ValueError('Add at least one product item.')
    return rows


@staff_permission_required('can_manage_purchases')
def purchase_list(request):
    purchases = Purchase.objects.select_related('tenant', 'supplier', 'created_by').prefetch_related('items__product').order_by('-purchase_date', '-id')
    if request.user.role != 'SUPER_ADMIN': purchases = purchases.filter(tenant=request.user.tenant)
    return render(request, 'purchases/purchase_list.html', {'purchases': purchases})


@staff_permission_required('can_manage_purchases')
def purchase_add(request):
    tenants = _tenant_options(request)
    suppliers = Supplier.objects.select_related('tenant').all() if request.user.role == 'SUPER_ADMIN' else Supplier.objects.filter(tenant=request.user.tenant)
    products = Product.objects.select_related('tenant').all() if request.user.role == 'SUPER_ADMIN' else Product.objects.filter(tenant=request.user.tenant)
    context = {'tenants': tenants, 'suppliers': suppliers, 'products': products, 'today': timezone.now().date()}
    if request.method == 'POST':
        try:
            rows = _rows(request.POST, 'unit_costs')
        except ValueError as exc:
            context['error'] = str(exc); return render(request, 'purchases/purchase_add.html', context)
        tenant = get_object_or_404(Tenant, id=request.POST.get('tenant'), is_active=True) if request.user.role == 'SUPER_ADMIN' else request.user.tenant
        supplier = get_object_or_404(Supplier, id=request.POST.get('supplier'), tenant=tenant)
        purchase_date = request.POST.get('purchase_date') or timezone.now().date()
        product_ids = [r[0] for r in rows]
        products_map = {p.id: p for p in Product.objects.filter(id__in=product_ids, tenant=tenant)}
        if len(products_map) != len(set(product_ids)):
            context['error'] = 'One or more selected products do not belong to this tenant.'; return render(request, 'purchases/purchase_add.html', context)
        with transaction.atomic():
            locked = {p.id: Product.objects.select_for_update().get(pk=p.id) for p in products_map.values()}
            total = sum((price * qty for _, qty, price in rows), Decimal('0'))
            purchase = Purchase.objects.create(tenant=tenant, supplier=supplier, purchase_date=purchase_date, total_amount=total, created_by=request.user)
            for pid, qty, unit_cost in rows:
                product = locked[pid]
                subtotal = unit_cost * qty
                PurchaseItem.objects.create(purchase=purchase, product=product, quantity=qty, unit_cost=unit_cost, subtotal=subtotal)
                product.stock_quantity += qty; product.save(update_fields=['stock_quantity'])
                Inventory.objects.update_or_create(tenant=tenant, product=product, defaults={'quantity': product.stock_quantity})
                StockTransaction.objects.create(tenant=tenant, product=product, transaction_type='PURCHASE', quantity=qty)
        return redirect('purchase_list')
    return render(request, 'purchases/purchase_add.html', context)
