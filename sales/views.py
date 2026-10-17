from decimal import Decimal, InvalidOperation
from django.db import transaction
from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import Sale, SaleItem
from tenants.models import Tenant
from customers.models import Customer
from products.models import Product
from inventory.models import Inventory, StockTransaction
from accounts.decorators import role_required, staff_permission_required


def _tenant_options(request):
    return Tenant.objects.filter(id=request.user.tenant_id, is_active=True) if request.user.role != 'SUPER_ADMIN' else Tenant.objects.filter(is_active=True).order_by('name')


def _sale_rows(post):
    ids = post.getlist('product_ids'); qtys = post.getlist('quantities'); prices = post.getlist('unit_prices')
    if not ids and post.get('product'): ids = [post.get('product')]
    if not qtys and post.get('quantity'): qtys = [post.get('quantity')]
    if not prices and post.get('unit_price'): prices = [post.get('unit_price')]
    rows=[]
    for i,pid in enumerate(ids):
        if not pid: continue
        try:
            qty=int(qtys[i]); price=Decimal(prices[i])
            if qty<=0 or price<0: raise ValueError
        except (IndexError, TypeError, ValueError, InvalidOperation):
            raise ValueError('Every item must have a valid positive quantity and non-negative price.')
        rows.append((int(pid),qty,price))
    if not rows: raise ValueError('Add at least one product item.')
    return rows


@role_required('SUPER_ADMIN', 'BUSINESS_OWNER', 'STAFF')
def sale_list(request):
    sales = Sale.objects.select_related('tenant','customer','created_by').prefetch_related('items__product').order_by('-sale_date','-id')
    if request.user.role != 'SUPER_ADMIN': sales=sales.filter(tenant=request.user.tenant)
    return render(request,'sales/sale_list.html',{'sales':sales})


@staff_permission_required('can_manage_sales')
def sale_add(request):
    tenants=_tenant_options(request)
    customers=Customer.objects.select_related('tenant').all() if request.user.role=='SUPER_ADMIN' else Customer.objects.filter(tenant=request.user.tenant)
    products=Product.objects.select_related('tenant').all() if request.user.role=='SUPER_ADMIN' else Product.objects.filter(tenant=request.user.tenant)
    context={'tenants':tenants,'customers':customers,'products':products,'today':timezone.now().date()}
    if request.method=='POST':
        try: rows=_sale_rows(request.POST)
        except ValueError as exc: context['error']=str(exc); return render(request,'sales/sale_add.html',context)
        tenant=get_object_or_404(Tenant,id=request.POST.get('tenant'),is_active=True) if request.user.role=='SUPER_ADMIN' else request.user.tenant
        customer_id=request.POST.get('customer') or None
        customer=get_object_or_404(Customer,id=customer_id,tenant=tenant) if customer_id else None
        sale_date=request.POST.get('sale_date') or timezone.now().date()
        product_ids=[r[0] for r in rows]
        products_map={p.id:p for p in Product.objects.filter(id__in=product_ids,tenant=tenant)}
        if len(products_map)!=len(set(product_ids)):
            context['error']='One or more selected products do not belong to this tenant.'; return render(request,'sales/sale_add.html',context)
        with transaction.atomic():
            locked={p.id:Product.objects.select_for_update().get(pk=p.id) for p in products_map.values()}
            required={}
            for pid,qty,_ in rows: required[pid]=required.get(pid,0)+qty
            for pid,qty in required.items():
                if locked[pid].stock_quantity<qty:
                    context['error']=f'Not enough stock for {locked[pid].name}. Available: {locked[pid].stock_quantity}.'; return render(request,'sales/sale_add.html',context)
            total=sum((price*qty for _,qty,price in rows),Decimal('0'))
            sale=Sale.objects.create(tenant=tenant,customer=customer,sale_date=sale_date,total_amount=total,created_by=request.user)
            for pid,qty,unit_price in rows:
                product=locked[pid]; subtotal=unit_price*qty
                SaleItem.objects.create(sale=sale,product=product,quantity=qty,unit_price=unit_price,subtotal=subtotal)
                product.stock_quantity-=qty; product.save(update_fields=['stock_quantity'])
                Inventory.objects.update_or_create(tenant=tenant,product=product,defaults={'quantity':product.stock_quantity})
                StockTransaction.objects.create(tenant=tenant,product=product,transaction_type='SALE',quantity=qty)
        return redirect('sale_detail', id=sale.id)
    return render(request,'sales/sale_add.html',context)


@role_required('SUPER_ADMIN','BUSINESS_OWNER','STAFF')
def sale_detail(request,id):
    sale=get_object_or_404(Sale.objects.select_related('tenant','customer','created_by').prefetch_related('items__product'),id=id) if request.user.role=='SUPER_ADMIN' else get_object_or_404(Sale.objects.select_related('tenant','customer','created_by').prefetch_related('items__product'),id=id,tenant=request.user.tenant)
    return render(request,'sales/sale_detail.html',{'sale':sale})


@role_required('SUPER_ADMIN','BUSINESS_OWNER','STAFF')
def invoice_view(request,id):
    sale=get_object_or_404(Sale.objects.select_related('tenant','customer','created_by').prefetch_related('items__product'),id=id) if request.user.role=='SUPER_ADMIN' else get_object_or_404(Sale.objects.select_related('tenant','customer','created_by').prefetch_related('items__product'),id=id,tenant=request.user.tenant)
    return render(request,'sales/invoice.html',{'sale':sale,'invoice_number':f'INV-{sale.id:06d}'})
