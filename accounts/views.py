from django.contrib.auth import authenticate, login, logout, password_validation
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import transaction
from django.db.models import Sum
from django.shortcuts import render, redirect, get_object_or_404

from tenants.models import Tenant
from .models import User
from products.models import Product
from suppliers.models import Supplier
from customers.models import Customer
from purchases.models import Purchase
from sales.models import Sale
from inventory.models import Inventory, StockTransaction
from .decorators import role_required


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        user = authenticate(request, username=request.POST.get('username', '').strip(), password=request.POST.get('password', ''))
        if user is not None and user.is_active:
            login(request, user)
            return redirect('dashboard')
        return render(request, 'accounts/login.html', {'error': 'Invalid username or password.'})
    return render(request, 'accounts/login.html')


def owner_register(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    if request.method == 'POST':
        tenant_name = request.POST.get('tenant_name', '').strip()
        tenant_email = request.POST.get('tenant_email', '').strip()
        phone = request.POST.get('phone', '').strip()
        address = request.POST.get('address', '').strip()
        username = request.POST.get('username', '').strip()
        email = request.POST.get('email', '').strip()
        password = request.POST.get('password', '')
        confirm_password = request.POST.get('confirm_password', '')
        errors = []
        if not tenant_name or not tenant_email or not username or not email or not password:
            errors.append('Please fill in all required fields.')
        if password != confirm_password:
            errors.append('Passwords do not match.')
        if not errors:
            try:
                password_validation.validate_password(password)
            except Exception as exc:
                errors.extend(exc.messages)
        if User.objects.filter(username=username).exists():
            errors.append('Username already exists.')
        if Tenant.objects.filter(email=tenant_email).exists():
            errors.append('A tenant with this email already exists.')
        if User.objects.filter(email=email).exists():
            errors.append('Owner email is already registered.')
        if errors:
            return render(request, 'accounts/register.html', {'errors': errors, 'form_data': request.POST})
        with transaction.atomic():
            tenant = Tenant.objects.create(name=tenant_name, email=tenant_email, phone=phone, address=address)
            User.objects.create_user(username=username, email=email, password=password, role='BUSINESS_OWNER', tenant=tenant)
        messages.success(request, 'Registration successful. Please log in with your owner account.')
        return redirect('login')
    return render(request, 'accounts/register.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


@login_required
def dashboard_view(request):
    user = request.user
    if user.role == 'SUPER_ADMIN':
        tenant_qs = Tenant.objects.filter(is_active=True)
        product_qs, supplier_qs, customer_qs = Product.objects.all(), Supplier.objects.all(), Customer.objects.all()
        purchase_qs, sale_qs, inventory_qs = Purchase.objects.all(), Sale.objects.all(), Inventory.objects.all()
        dashboard_title = 'Super Admin Dashboard'
    else:
        tenant = user.tenant
        product_qs = Product.objects.filter(tenant=tenant) if tenant else Product.objects.none()
        supplier_qs = Supplier.objects.filter(tenant=tenant) if tenant else Supplier.objects.none()
        customer_qs = Customer.objects.filter(tenant=tenant) if tenant else Customer.objects.none()
        purchase_qs = Purchase.objects.filter(tenant=tenant) if tenant else Purchase.objects.none()
        sale_qs = Sale.objects.filter(tenant=tenant) if tenant else Sale.objects.none()
        inventory_qs = Inventory.objects.filter(tenant=tenant) if tenant else Inventory.objects.none()
        tenant_qs = Tenant.objects.filter(pk=user.tenant_id) if user.tenant_id else Tenant.objects.none()
        dashboard_title = 'Business Owner Dashboard' if user.role == 'BUSINESS_OWNER' else 'Staff Dashboard'
    low_stock_count = sum(1 for item in inventory_qs.select_related('product') if item.quantity <= item.product.reorder_level)
    total_stock = inventory_qs.aggregate(total=Sum('quantity'))['total'] or 0
    context = {
        'tenant_count': tenant_qs.count(), 'product_count': product_qs.count(), 'supplier_count': supplier_qs.count(),
        'customer_count': customer_qs.count(), 'purchase_count': purchase_qs.count(), 'sale_count': sale_qs.count(),
        'total_stock': total_stock, 'low_stock_count': low_stock_count,
        'recent_transactions': StockTransaction.objects.filter(tenant__in=tenant_qs).select_related('product', 'tenant')[:8],
        'dashboard_title': dashboard_title,
    }
    return render(request, 'accounts/dashboard.html', context)


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def staff_list(request):
    users = User.objects.filter(tenant=request.user.tenant, role='STAFF').select_related('tenant').order_by('username') if request.user.role == 'BUSINESS_OWNER' else User.objects.filter(role='STAFF').select_related('tenant').order_by('tenant__name', 'username')
    return render(request, 'accounts/staff_list.html', {'users': users})


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def staff_add(request):
    if request.user.role == 'SUPER_ADMIN':
        tenants = Tenant.objects.filter(is_active=True).order_by('name')
    else:
        tenants = Tenant.objects.filter(id=request.user.tenant_id, is_active=True)
    if request.method == 'POST':
        tenant = get_object_or_404(Tenant, id=request.POST.get('tenant'), is_active=True) if request.user.role == 'SUPER_ADMIN' else request.user.tenant
        username = request.POST.get('username', '').strip(); email = request.POST.get('email', '').strip(); password = request.POST.get('password', '')
        if not username or not password:
            return render(request, 'accounts/staff_form.html', {'tenants': tenants, 'error': 'Username and password are required.'})
        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/staff_form.html', {'tenants': tenants, 'error': 'Username already exists.'})
        User.objects.create_user(username=username, email=email, password=password, role='STAFF', tenant=tenant,
            can_manage_products='can_manage_products' in request.POST, can_manage_purchases='can_manage_purchases' in request.POST,
            can_manage_sales='can_manage_sales' in request.POST, can_manage_customers='can_manage_customers' in request.POST,
            can_view_reports='can_view_reports' in request.POST)
        messages.success(request, 'Staff account created successfully.')
        return redirect('staff_list')
    return render(request, 'accounts/staff_form.html', {'tenants': tenants})


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER')
def staff_edit(request, id):
    staff = get_object_or_404(User, id=id, role='STAFF') if request.user.role == 'SUPER_ADMIN' else get_object_or_404(User, id=id, role='STAFF', tenant=request.user.tenant)
    if request.method == 'POST':
        staff.email = request.POST.get('email', '').strip()
        staff.can_manage_products = 'can_manage_products' in request.POST
        staff.can_manage_purchases = 'can_manage_purchases' in request.POST
        staff.can_manage_sales = 'can_manage_sales' in request.POST
        staff.can_manage_customers = 'can_manage_customers' in request.POST
        staff.can_view_reports = 'can_view_reports' in request.POST
        if request.POST.get('password'):
            staff.set_password(request.POST['password'])
        staff.save()
        messages.success(request, 'Staff permissions updated.')
        return redirect('staff_list')
    return render(request, 'accounts/staff_form.html', {'staff': staff, 'edit_mode': True, 'tenants': Tenant.objects.filter(id=staff.tenant_id)})


@role_required('SUPER_ADMIN')
def user_list(request):
    users = User.objects.select_related('tenant').order_by('username')
    return render(request, 'accounts/user_list.html', {'users': users})


@role_required('SUPER_ADMIN')
def user_add(request):
    tenants = Tenant.objects.filter(is_active=True).order_by('name')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip(); email = request.POST.get('email', '').strip(); password = request.POST.get('password', ''); role = request.POST.get('role'); tenant_id = request.POST.get('tenant')
        if User.objects.filter(username=username).exists():
            return render(request, 'accounts/user_form.html', {'tenants': tenants, 'error': 'Username already exists.'})
        if role not in dict(User.ROLE_CHOICES):
            return render(request, 'accounts/user_form.html', {'tenants': tenants, 'error': 'Invalid role.'})
        tenant = get_object_or_404(Tenant, id=tenant_id, is_active=True) if tenant_id else None
        if role == 'SUPER_ADMIN': tenant = None
        elif tenant is None:
            return render(request, 'accounts/user_form.html', {'tenants': tenants, 'error': 'A tenant is required for Business Owner and Staff.'})
        User.objects.create_user(username=username, email=email, password=password, role=role, tenant=tenant)
        return redirect('user_list')
    return render(request, 'accounts/user_form.html', {'tenants': tenants})
