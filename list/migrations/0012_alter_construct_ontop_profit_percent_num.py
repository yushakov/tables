# Generated by Django 4.2.4 on 2024-01-24 17:13

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0011_construct_notes_txt_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='construct',
            name='ontop_profit_percent_num',
            field=models.FloatField(default=0, validators=[django.core.validators.MinValueValidator(0), django.core.validators.MaxValueValidator(100)]),
        ),
    ]
