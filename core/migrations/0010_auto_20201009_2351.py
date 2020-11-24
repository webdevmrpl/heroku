# Generated by Django 3.1.1 on 2020-10-09 20:51

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0009_auto_20201006_2111'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='purchases',
        ),
        migrations.AddField(
            model_name='purchase',
            name='customer',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.PROTECT, to='core.customer', verbose_name='Покупатель'),
        ),
    ]
