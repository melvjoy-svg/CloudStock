from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('accounts', '0001_initial')]
    operations = [
        migrations.AddField(model_name='user', name='can_manage_products', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='user', name='can_manage_purchases', field=models.BooleanField(default=False)),
        migrations.AddField(model_name='user', name='can_manage_sales', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='user', name='can_manage_customers', field=models.BooleanField(default=True)),
        migrations.AddField(model_name='user', name='can_view_reports', field=models.BooleanField(default=False)),
    ]
