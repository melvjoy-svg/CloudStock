from datetime import datetime, timedelta
from decimal import Decimal
from django.contrib.auth.decorators import login_required
from django.db.models import Sum, F
from django.shortcuts import render, redirect
from accounts.decorators import staff_permission_required
from sales.models import Sale, SaleItem
from purchases.models import Purchase, PurchaseItem
from products.models import Product
from inventory.models import Inventory


@staff_permission_required('can_view_reports')
def reports_dashboard(request):
    if request.user.role == 'SUPER_ADMIN':
        sales=Sale.objects.all(); purchases=Purchase.objects.all(); inventory=Inventory.objects.all()
    else:
        sales=Sale.objects.filter(tenant=request.user.tenant); purchases=Purchase.objects.filter(tenant=request.user.tenant); inventory=Inventory.objects.filter(tenant=request.user.tenant)
    today=datetime.now().date(); start_raw=request.GET.get('start'); end_raw=request.GET.get('end')
    try: start=datetime.strptime(start_raw,'%Y-%m-%d').date() if start_raw else today-timedelta(days=30)
    except ValueError: start=today-timedelta(days=30)
    try: end=datetime.strptime(end_raw,'%Y-%m-%d').date() if end_raw else today
    except ValueError: end=today
    if start>end: start,end=end,start
    sales=sales.filter(sale_date__range=(start,end)); purchases=purchases.filter(purchase_date__range=(start,end))
    sales_total=sales.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    purchases_total=purchases.aggregate(total=Sum('total_amount'))['total'] or Decimal('0')
    top_products=(SaleItem.objects.filter(sale__in=sales).values('product__name').annotate(quantity=Sum('quantity'), revenue=Sum('subtotal')).order_by('-revenue')[:10])
    low_stock=inventory.filter(quantity__lte=F('product__reorder_level')).select_related('product').order_by('quantity')[:10]
    context={'start':start,'end':end,'sales':sales.order_by('-sale_date','-id')[:20],'purchases':purchases.order_by('-purchase_date','-id')[:20], 'sales_total':sales_total,'purchases_total':purchases_total,'profit_estimate':sales_total-purchases_total,'sales_count':sales.count(),'purchases_count':purchases.count(),'top_products':top_products,'low_stock':low_stock}
    return render(request,'reports/dashboard.html',context)
