# Generated by Django 3.2.23 on 2024-03-19 11:55

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('checkout', '0009_cart_stripe_pid'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Cart',
        ),
    ]