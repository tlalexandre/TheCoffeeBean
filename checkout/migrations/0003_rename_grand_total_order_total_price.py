# Generated by Django 3.2.23 on 2024-03-16 12:21

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0002_auto_20240316_1203'),
    ]

    operations = [
        migrations.RenameField(
            model_name='order',
            old_name='grand_total',
            new_name='total_price',
        ),
    ]
