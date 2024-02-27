# Generated by Django 3.2.23 on 2024-02-27 09:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('orderonline', '0016_ingredientoption_is_extra'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ingredientoption',
            old_name='is_extra',
            new_name='single_select',
        ),
        migrations.RemoveField(
            model_name='ingredient',
            name='option',
        ),
        migrations.RemoveField(
            model_name='ingredient',
            name='single_select',
        ),
        migrations.AddField(
            model_name='menuitemingredient',
            name='option',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='orderonline.ingredientoption'),
        ),
    ]
