# Generated by Django 3.2.23 on 2024-03-18 10:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0003_rename_grand_total_order_total_price'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='order',
            name='postcode',
        ),
    ]
