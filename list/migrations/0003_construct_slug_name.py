# Generated by Django 4.2.4 on 2023-09-02 08:54

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('list', '0002_historyrecord'),
    ]

    operations = [
        migrations.AddField(
            model_name='construct',
            name='slug_name',
            field=models.CharField(max_length=500, null=True),
        ),
    ]
