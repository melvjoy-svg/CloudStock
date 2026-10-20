from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from inventory.models import Inventory
from .models import Category, Product


@login_required
def product_list(request):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        products = Product.objects.select_related(
            'tenant', 'category'
        ).all().order_by('-id')
    else:
        products = Product.objects.select_related(
            'tenant', 'category'
        ).filter(tenant=user.tenant).order_by('-id')

    return render(request, 'products/product_list.html', {
        'products': products,
    })


@login_required
def product_add(request):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        tenants = user.__class__.objects.filter(
            role='BUSINESS_OWNER'
        ).exclude(tenant__isnull=True)

        selected_tenant_id = request.POST.get('tenant') or request.GET.get('tenant')

        tenant = None

        if selected_tenant_id:
            tenant = get_object_or_404(
                user.__class__.objects.filter(
                    role='BUSINESS_OWNER'
                ).exclude(tenant__isnull=True),
                tenant_id=selected_tenant_id
            ).tenant
    else:
        tenants = []
        tenant = user.tenant

    if request.method == 'POST':
        if user.role == 'SUPER_ADMIN':
            tenant_id = request.POST.get('tenant')

            if not tenant_id:
                return render(request, 'products/product_add.html', {
                    'error': 'Please select a business.',
                    'tenants': tenants,
                })

            owner = get_object_or_404(
                user.__class__.objects.filter(
                    role='BUSINESS_OWNER'
                ).exclude(tenant__isnull=True),
                tenant_id=tenant_id
            )

            tenant = owner.tenant

        if not tenant:
            return render(request, 'products/product_add.html', {
                'error': 'No business selected.',
                'tenants': tenants,
            })

        name = request.POST.get('name', '').strip()
        sku = request.POST.get('sku', '').strip()
        price = request.POST.get('price')
        cost_price = request.POST.get('cost_price')
        opening_stock = request.POST.get('stock_quantity', 0)
        reorder_level = request.POST.get('reorder_level', 0)
        description = request.POST.get('description', '').strip()
        category_id = request.POST.get('category')

        category = None

        if category_id:
            category = get_object_or_404(
                Category,
                id=category_id,
                tenant=tenant
            )

        product = Product.objects.create(
            tenant=tenant,
            category=category,
            name=name,
            sku=sku,
            price=price,
            cost_price=cost_price,
            stock_quantity=opening_stock,
            reorder_level=reorder_level,
            description=description,
            image=request.FILES.get('image')
        )

        Inventory.objects.update_or_create(
            tenant=tenant,
            product=product,
            defaults={
                'quantity': opening_stock
            }
        )

        return redirect('product_list')

    categories = Category.objects.filter(
        tenant=tenant
    ).order_by('name') if tenant else Category.objects.none()

    return render(request, 'products/product_add.html', {
        'tenants': tenants,
        'categories': categories,
        'tenant': tenant,
    })


@login_required
def product_edit(request, pk):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        product = get_object_or_404(Product, pk=pk)
    else:
        product = get_object_or_404(
            Product,
            pk=pk,
            tenant=user.tenant
        )

    if request.method == 'POST':
        product.name = request.POST.get('name', '').strip()
        product.sku = request.POST.get('sku', '').strip()
        product.price = request.POST.get('price')
        product.cost_price = request.POST.get('cost_price')
        product.reorder_level = request.POST.get('reorder_level', 0)
        product.description = request.POST.get(
            'description', ''
        ).strip()

        category_id = request.POST.get('category')

        if category_id:
            product.category = get_object_or_404(
                Category,
                id=category_id,
                tenant=product.tenant
            )
        else:
            product.category = None

        if request.FILES.get('image'):
            product.image = request.FILES.get('image')

        product.save()

        return redirect('product_list')

    categories = Category.objects.filter(
        tenant=product.tenant
    ).order_by('name')

    return render(request, 'products/product_edit.html', {
        'product': product,
        'categories': categories,
    })


@login_required
def product_delete(request, pk):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        product = get_object_or_404(Product, pk=pk)
    else:
        product = get_object_or_404(
            Product,
            pk=pk,
            tenant=user.tenant
        )

    if request.method == 'POST':
        product.delete()
        return redirect('product_list')

    return render(request, 'products/product_delete.html', {
        'product': product,
    })


@login_required
def category_list(request):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        categories = Category.objects.select_related(
            'tenant'
        ).all().order_by('-id')
    else:
        categories = Category.objects.filter(
            tenant=user.tenant
        ).order_by('-id')

    return render(request, 'products/category_list.html', {
        'categories': categories,
    })


@login_required
def category_add(request):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        tenants = user.__class__.objects.filter(
            role='BUSINESS_OWNER'
        ).exclude(tenant__isnull=True)
    else:
        tenants = []
    
    if request.method == 'POST':

        if user.role == 'SUPER_ADMIN':
            tenant_id = request.POST.get('tenant')

            if not tenant_id:
                return render(request, 'products/category_add.html', {
                    'error': 'Please select a business.',
                    'tenants': tenants,
                })

            owner = get_object_or_404(
                user.__class__.objects.filter(
                    role='BUSINESS_OWNER'
                ).exclude(tenant__isnull=True),
                tenant_id=tenant_id
            )

            tenant = owner.tenant

        else:
            tenant = user.tenant

        Category.objects.create(
            tenant=tenant,
            name=request.POST.get('name', '').strip(),
            description=request.POST.get(
                'description', ''
            ).strip()
        )

        return redirect('category_list')

    return render(request, 'products/category_add.html', {
        'tenants': tenants,
    })


@login_required
def category_edit(request, pk):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        category = get_object_or_404(Category, pk=pk)
    else:
        category = get_object_or_404(
            Category,
            pk=pk,
            tenant=user.tenant
        )

    if request.method == 'POST':
        category.name = request.POST.get('name', '').strip()
        category.description = request.POST.get(
            'description', ''
        ).strip()

        category.save()

        return redirect('category_list')

    return render(request, 'products/category_edit.html', {
        'category': category,
    })


@login_required
def category_delete(request, pk):
    user = request.user

    if user.role == 'SUPER_ADMIN':
        category = get_object_or_404(Category, pk=pk)
    else:
        category = get_object_or_404(
            Category,
            pk=pk,
            tenant=user.tenant
        )

    if request.method == 'POST':
        category.delete()
        return redirect('category_list')

    return render(request, 'products/category_delete.html', {
        'category': category,
    })
