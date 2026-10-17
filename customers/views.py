from django.shortcuts import render, redirect, get_object_or_404

from .models import Customer
from tenants.models import Tenant
from accounts.decorators import role_required , staff_permission_required, staff_permission_required


# =========================
# CUSTOMER LIST
# =========================

@role_required('SUPER_ADMIN', 'BUSINESS_OWNER', 'STAFF')
def customer_list(request):

    if request.user.role == 'SUPER_ADMIN':
        customers = Customer.objects.all().order_by('name')

    else:
        customers = Customer.objects.filter(
            tenant=request.user.tenant
        ).order_by('name')

    return render(
        request,
        'customers/customer_list.html',
        {'customers': customers}
    )


# =========================
# ADD CUSTOMER
# =========================

@staff_permission_required('can_manage_customers')
def customer_add(request):

    if request.user.role == 'SUPER_ADMIN':

        tenants = Tenant.objects.filter(
            is_active=True
        )

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

        # Super Admin can select tenant
        if request.user.role == 'SUPER_ADMIN':

            tenant_id = request.POST.get('tenant')

            tenant = get_object_or_404(
                Tenant,
                id=tenant_id,
                is_active=True
            )

        # Owner/Staff automatically use their tenant
        else:

            tenant = request.user.tenant

        Customer.objects.create(
            tenant=tenant,
            name=name,
            phone=phone,
            email=email,
            address=address
        )

        return redirect('customer_list')

    return render(
        request,
        'customers/customer_add.html',
        {'tenants': tenants}
    )


# =========================
# EDIT CUSTOMER
# =========================

@staff_permission_required('can_manage_customers')
def customer_edit(request, id):

    if request.user.role == 'SUPER_ADMIN':

        customer = get_object_or_404(
            Customer,
            id=id
        )

    else:

        customer = get_object_or_404(
            Customer,
            id=id,
            tenant=request.user.tenant
        )

    if request.method == 'POST':

        customer.name = request.POST.get('name')
        customer.phone = request.POST.get('phone')
        customer.email = request.POST.get('email')
        customer.address = request.POST.get('address')

        customer.save()

        return redirect('customer_list')

    return render(
        request,
        'customers/customer_edit.html',
        {'customer': customer}
    )


# =========================
# DELETE CUSTOMER
# =========================

@staff_permission_required('can_manage_customers')
def customer_delete(request, id):

    if request.user.role == 'SUPER_ADMIN':

        customer = get_object_or_404(
            Customer,
            id=id
        )

    else:

        customer = get_object_or_404(
            Customer,
            id=id,
            tenant=request.user.tenant
        )

    if request.method == 'POST':

        customer.delete()

        return redirect('customer_list')

    return render(
        request,
        'customers/customer_delete.html',
        {'customer': customer}
    )