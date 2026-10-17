# CloudStock AWS Deployment Preparation

## Recommended architecture
- AWS EC2: Django application + Gunicorn + Nginx
- AWS RDS MySQL: production database
- Optional S3: media/static assets if the project grows

## Before deployment
1. Create RDS MySQL database and user.
2. Set the variables in `.env` from `.env.example`.
3. Install `requirements.txt`.
4. Run `python manage.py migrate`.
5. Run `python manage.py collectstatic --noinput`.
6. Create the production superuser.
7. Set `DJANGO_DEBUG=False` and correct `DJANGO_ALLOWED_HOSTS`.
8. Put Nginx in front of Gunicorn and enable HTTPS.

## Multi-tenant deployment note
CloudStock keeps one shared relational schema. New tenants do not require new databases or tables; tenant-owned records are isolated with foreign keys and tenant-aware query filtering.
