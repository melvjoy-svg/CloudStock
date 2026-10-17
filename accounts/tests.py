from decimal import Decimal
from django.test import TestCase
from django.urls import reverse

from tenants.models import Tenant
from accounts.models import User
from products.models import Category, Product
from suppliers.models import Supplier
from customers.models import Customer
from inventory.models import Inventory, StockTransaction
from purchases.models import Purchase
from sales.models import Sale


class CloudStockTenantIsolationTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.t1 = Tenant.objects.create(name='Tenant A', email='a@test.com')
        cls.t2 = Tenant.objects.create(name='Tenant B', email='b@test.com')

        cls.owner1 = User.objects.create_user(
            username='owner1', password='pass12345',
            role='BUSINESS_OWNER', tenant=cls.t1
        )
        cls.owner2 = User.objects.create_user(
            username='owner2', password='pass12345',
            role='BUSINESS_OWNER', tenant=cls.t2
        )
        cls.superuser = User.objects.create_user(
            username='admin', password='pass12345',
            role='SUPER_ADMIN'
        )

        c1 = Category.objects.create(tenant=cls.t1, name='A Category')
        c2 = Category.objects.create(tenant=cls.t2, name='B Category')
        cls.p1 = Product.objects.create(
            tenant=cls.t1, category=c1, name='A Product', sku='A-001',
            price=Decimal('100'), cost_price=Decimal('70'), stock_quantity=10,
            reorder_level=2
        )
        cls.p2 = Product.objects.create(
            tenant=cls.t2, category=c2, name='B Product', sku='B-001',
            price=Decimal('200'), cost_price=Decimal('150'), stock_quantity=20,
            reorder_level=3
        )
        Inventory.objects.create(tenant=cls.t1, product=cls.p1, quantity=10)
        Inventory.objects.create(tenant=cls.t2, product=cls.p2, quantity=20)
        cls.s1 = Supplier.objects.create(tenant=cls.t1, name='A Supplier', phone='1')
        cls.s2 = Supplier.objects.create(tenant=cls.t2, name='B Supplier', phone='2')
        cls.cust1 = Customer.objects.create(tenant=cls.t1, name='A Customer', phone='1')
        cls.cust2 = Customer.objects.create(tenant=cls.t2, name='B Customer', phone='2')

    def test_owner_sees_only_own_products(self):
        self.client.force_login(self.owner1)
        response = self.client.get(reverse('product_list'))
        self.assertContains(response, 'A Product')
        self.assertNotContains(response, 'B Product')

    def test_owner_sees_only_own_customers(self):
        self.client.force_login(self.owner1)
        response = self.client.get(reverse('customer_list'))
        self.assertContains(response, 'A Customer')
        self.assertNotContains(response, 'B Customer')

    def test_owner_cannot_open_other_tenant_product(self):
        self.client.force_login(self.owner1)
        response = self.client.get(reverse('product_edit', args=[self.p2.id]))
        self.assertEqual(response.status_code, 404)

    def test_owner_cannot_create_sale_using_other_tenant_product(self):
        self.client.force_login(self.owner1)
        response = self.client.post(reverse('sale_add'), {
            'tenant': self.t1.id,
            'customer': self.cust1.id,
            'product': self.p2.id,
            'quantity': 1,
            'unit_price': '200',
            'sale_date': '2026-09-30',
        })
        self.assertEqual(response.status_code, 404)
        self.assertEqual(Sale.objects.count(), 0)

    def test_purchase_increases_stock_and_creates_transaction(self):
        self.client.force_login(self.owner1)
        response = self.client.post(reverse('purchase_add'), {
            'tenant': self.t1.id,
            'supplier': self.s1.id,
            'product': self.p1.id,
            'quantity': 5,
            'unit_cost': '70',
            'purchase_date': '2026-09-30',
        })
        self.assertRedirects(response, reverse('purchase_list'))
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, 15)
        self.assertEqual(Inventory.objects.get(product=self.p1).quantity, 15)
        self.assertEqual(
            StockTransaction.objects.filter(
                product=self.p1, transaction_type='PURCHASE'
            ).count(), 1
        )

    def test_sale_decreases_stock(self):
        self.client.force_login(self.owner1)
        response = self.client.post(reverse('sale_add'), {
            'tenant': self.t1.id,
            'customer': self.cust1.id,
            'product': self.p1.id,
            'quantity': 3,
            'unit_price': '100',
            'sale_date': '2026-09-30',
        })
        self.assertRedirects(response, reverse('sale_list'))
        self.p1.refresh_from_db()
        self.assertEqual(self.p1.stock_quantity, 7)
        self.assertEqual(Inventory.objects.get(product=self.p1).quantity, 7)

    def test_staff_cannot_manage_products(self):
        staff = User.objects.create_user(
            username='staff1', password='pass12345',
            role='STAFF', tenant=self.t1
        )
        self.client.force_login(staff)
        response = self.client.get(reverse('product_add'))
        self.assertRedirects(response, reverse('dashboard'))

    def test_non_superuser_cannot_manage_tenants(self):
        self.client.force_login(self.owner1)
        response = self.client.get(reverse('tenant_list'))
        self.assertRedirects(response, reverse('dashboard'))
