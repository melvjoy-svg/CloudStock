from django.shortcuts import render, redirect, get_object_or_404

from .models import Supplier
from tenants.models import Tenant
from accounts.decorators import role_required


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def supplier_list(request):

    if request.user.role == 'SUPER_ADMIN':
        suppliers = Supplier.objects.all()
    else:
        suppliers = Supplier.objects.filter(
            tenant=request.user.tenant
        )

    return render(
        request,
        'suppliers/supplier_list.html',
        {'suppliers': suppliers}
    )


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def supplier_add(request):

    if request.user.role == 'SUPER_ADMIN':
        tenants = Tenant.objects.filter(is_active=True)
    else:
        tenants = Tenant.objects.filter(
            id=request.user.tenant_id,
            is_active=True
        )

    if request.method == 'POST':

        name = request.POST.get('name')
        phone = request.POST.get('phone')
        email = request.POST.get('email')
        address = request.POST.get('address')

        if request.user.role == 'SUPER_ADMIN':
            tenant_id = request.POST.get('tenant')

            tenant = get_object_or_404(
                Tenant,
                id=tenant_id,
                is_active=True
            )
        else:
            tenant = request.user.tenant

        Supplier.objects.create(
            tenant=tenant,
            name=name,
            phone=phone,
            email=email,
            address=address
        )

        return redirect('supplier_list')

    return render(
        request,
        'suppliers/supplier_add.html',
        {'tenants': tenants}
    )


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def supplier_edit(request, id):

    if request.user.role == 'SUPER_ADMIN':
        supplier = get_object_or_404(
            Supplier,
            id=id
        )
    else:
        supplier = get_object_or_404(
            Supplier,
            id=id,
            tenant=request.user.tenant
        )

    if request.method == 'POST':

        supplier.name = request.POST.get('name')
        supplier.phone = request.POST.get('phone')
        supplier.email = request.POST.get('email')
        supplier.address = request.POST.get('address')

        supplier.save()

        return redirect('supplier_list')

    return render(
        request,
        'suppliers/supplier_edit.html',
        {'supplier': supplier}
    )


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def supplier_delete(request, id):

    if request.user.role == 'SUPER_ADMIN':
        supplier = get_object_or_404(
            Supplier,
            id=id
        )
    else:
        supplier = get_object_or_404(
            Supplier,
            id=id,
            tenant=request.user.tenant
        )

    if request.method == 'POST':
        supplier.delete()
        return redirect('supplier_list')

    return render(
        request,
        'suppliers/supplier_delete.html',
        {'supplier': supplier}
    )