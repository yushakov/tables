# Generated by Django 4.2.4 on 2023-11-13 23:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0006_alter_category_options_invoice_owner'),
    ]

    operations = [
        migrations.AddField(
            model_name='construct',
            name='foreman',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL),
        ),
    ]
