# Generated by Django 4.2.4 on 2024-01-30 21:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0012_alter_construct_ontop_profit_percent_num'),
    ]

    operations = [
        migrations.AddField(
            model_name='construct',
            name='footer_txt',
            field=models.TextField(blank=True, default='', null=True),
        ),
        migrations.AddField(
            model_name='construct',
            name='header_txt',
            field=models.TextField(blank=True, default='QUOTE', null=True),
        ),
    ]
