from django.shortcuts import render, redirect, get_object_or_404
from accounts.decorators import role_required
from .models import Tenant


@role_required('SUPER_ADMIN')
def tenant_list(request):
    tenants = Tenant.objects.all().order_by('name')
    return render(request, 'tenants/tenant_list.html', {'tenants': tenants})


@role_required('SUPER_ADMIN')
def tenant_add(request):
    if request.method == 'POST':
        Tenant.objects.create(
            name=request.POST.get('name', '').strip(),
            email=request.POST.get('email', '').strip(),
            phone=request.POST.get('phone', '').strip(),
            address=request.POST.get('address', '').strip(),
        )
        return redirect('tenant_list')
    return render(request, 'tenants/tenant_form.html')


@role_required('SUPER_ADMIN')
def tenant_edit(request, id):
    tenant = get_object_or_404(Tenant, id=id)
    if request.method == 'POST':
        tenant.name = request.POST.get('name', '').strip()
        tenant.email = request.POST.get('email', '').strip()
        tenant.phone = request.POST.get('phone', '').strip()
        tenant.address = request.POST.get('address', '').strip()
        tenant.is_active = request.POST.get('is_active') == 'on'
        tenant.save()
        return redirect('tenant_list')
    return render(request, 'tenants/tenant_form.html', {'tenant': tenant})


@role_required('SUPER_ADMIN')
def tenant_delete(request, id):
    tenant = get_object_or_404(Tenant, id=id)
    if request.method == 'POST':
        tenant.delete()
        return redirect('tenant_list')
    return render(
        request, 'tenants/tenant_confirm_delete.html', {'tenant': tenant}
    )
