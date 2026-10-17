# CloudStock – Multi-Tenant SaaS Inventory Management System

CloudStock is a Django + MySQL multi-tenant inventory, purchasing and sales management system.

## Main Features
- Business Owner self-registration with automatic tenant creation
- Role-based access: Super Admin, Business Owner, Staff
- Staff-level module permissions
- Tenant-isolated products, suppliers, customers, purchases, sales and inventory
- Category and Product management
- Multi-item Purchase Entry with automatic stock increase
- Multi-item Sales Entry with stock validation and automatic stock decrease
- Inventory and Stock Transaction history
- Printable invoice for every sale
- Sales / Purchase / low-stock reports
- Dashboard statistics
- MySQL relational database with PK/FK relationships and normalized entities
- AWS deployment preparation files

## Local Run
```powershell
python -m venv venv
venv\\Scripts\\activate
pip install -r requirements.txt
python manage.py migrate
python manage.py createsuperuser
python manage.py runserver
```

For the existing local MySQL setup, configure `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, and `DB_PORT` as needed. `.env.example` is provided for deployment configuration.

## Multi-Tenant Design
CloudStock uses a shared database/shared schema. Tenant-owned records carry a `tenant_id` foreign key and views filter records by the logged-in user's tenant. A new business therefore does not require new tables or a new database.

## AWS Preparation
See `AWS_DEPLOYMENT.md` and `.env.example` for production configuration guidance.
