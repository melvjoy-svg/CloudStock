from django.contrib import messages
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404

from .models import Product, Category
from tenants.models import Tenant
from inventory.models import Inventory, StockTransaction
from accounts.decorators import role_required , staff_permission_required, staff_permission_required


def tenant_for_user(request, tenant_id=None):
    if request.user.role == 'SUPER_ADMIN':
        return get_object_or_404(Tenant, id=tenant_id, is_active=True)
    return request.user.tenant


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER', 'STAFF')
def product_list(request):
    products = Product.objects.select_related('tenant', 'category')
    if request.user.role != 'SUPER_ADMIN':
        products = products.filter(tenant=request.user.tenant)
    return render(request, 'products/product_list.html', {'products': products})


@staff_permission_required('can_manage_products')
def product_add(request):
    tenants = Tenant.objects.filter(is_active=True) if request.user.role == 'SUPER_ADMIN' else Tenant.objects.filter(id=request.user.tenant_id, is_active=True)
    categories = Category.objects.filter(tenant__in=tenants).order_by('name')

    if request.method == 'POST':
        tenant = tenant_for_user(request, request.POST.get('tenant'))
        category_id = request.POST.get('category') or None
        category = None
        if category_id:
            category = get_object_or_404(Category, id=category_id, tenant=tenant)

        try:
            opening_stock = int(request.POST.get('stock_quantity', 0))
            reorder_level = int(request.POST.get('reorder_level', 0))
            if opening_stock < 0 or reorder_level < 0:
                raise ValueError
        except (TypeError, ValueError):
            return render(request, 'products/product_add.html', {
                'tenants': tenants, 'categories': categories,
                'error': 'Stock and reorder level must be non-negative integers.'
            })

        with transaction.atomic():
            product = Product.objects.create(
                tenant=tenant,
                category=category,
                name=request.POST.get('name', '').strip(),
                sku=request.POST.get('sku', '').strip(),
                price=request.POST.get('price'),
                cost_price=request.POST.get('cost_price'),
                stock_quantity=opening_stock,
                reorder_level=reorder_level,
                description=request.POST.get('description', '').strip()
            )
            Inventory.objects.update_or_create(
                tenant=tenant, product=product,
                defaults={'quantity': opening_stock}
            )
            if opening_stock:
                StockTransaction.objects.create(
                    tenant=tenant, product=product,
                    transaction_type='ADJUSTMENT', quantity=opening_stock
                )
        return redirect('product_list')

    return render(request, 'products/product_add.html', {
        'tenants': tenants, 'categories': categories
    })


@staff_permission_required('can_manage_products')
def product_edit(request, id):
    product = get_object_or_404(
        Product, id=id
    ) if request.user.role == 'SUPER_ADMIN' else get_object_or_404(
        Product, id=id, tenant=request.user.tenant
    )
    categories = Category.objects.filter(tenant=product.tenant).order_by('name')

    if request.method == 'POST':
        category_id = request.POST.get('category') or None
        product.category = get_object_or_404(
            Category, id=category_id, tenant=product.tenant
        ) if category_id else None
        product.name = request.POST.get('name', '').strip()
        product.sku = request.POST.get('sku', '').strip()
        product.price = request.POST.get('price')
        product.cost_price = request.POST.get('cost_price')
        product.reorder_level = int(request.POST.get('reorder_level', product.reorder_level))
        product.description = request.POST.get('description', '').strip()
        product.save()
        return redirect('product_list')

    return render(request, 'products/product_edit.html', {
        'product': product, 'categories': categories
    })


@staff_permission_required('can_manage_products')
def product_delete(request, id):
    product = get_object_or_404(Product, id=id) if request.user.role == 'SUPER_ADMIN' else get_object_or_404(Product, id=id, tenant=request.user.tenant)
    if request.method == 'POST':
        product.delete()
        return redirect('product_list')
    return render(request, 'products/product_delete.html', {'product': product})


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER', 'STAFF')
def category_list(request):
    categories = Category.objects.all()
    if request.user.role != 'SUPER_ADMIN':
        categories = categories.filter(tenant=request.user.tenant)
    return render(request, 'products/category_list.html', {'categories': categories})


@staff_permission_required('can_manage_products')
def category_add(request):
    tenants = Tenant.objects.filter(is_active=True) if request.user.role == 'SUPER_ADMIN' else Tenant.objects.filter(id=request.user.tenant_id, is_active=True)
    if request.method == 'POST':
        tenant = tenant_for_user(request, request.POST.get('tenant'))
        Category.objects.create(
            tenant=tenant,
            name=request.POST.get('name', '').strip(),
            description=request.POST.get('description', '').strip()
        )
        return redirect('category_list')
    return render(request, 'products/category_add.html', {'tenants': tenants})


@staff_permission_required('can_manage_products')
def category_edit(request, id):
    category = get_object_or_404(Category, id=id) if request.user.role == 'SUPER_ADMIN' else get_object_or_404(Category, id=id, tenant=request.user.tenant)
    if request.method == 'POST':
        category.name = request.POST.get('name', '').strip()
        category.description = request.POST.get('description', '').strip()
        category.save()
        return redirect('category_list')
    return render(request, 'products/category_edit.html', {'category': category})


@staff_permission_required('can_manage_products')
def category_delete(request, id):
    category = get_object_or_404(Category, id=id) if request.user.role == 'SUPER_ADMIN' else get_object_or_404(Category, id=id, tenant=request.user.tenant)
    if request.method == 'POST':
        category.delete()
        return redirect('category_list')
    return render(request, 'products/category_delete.html', {'category': category})
