# Generated by Django 3.1.2 on 2020-11-22 21:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_totalpurchases'),
    ]

    operations = [
        migrations.AddField(
            model_name='totalpurchases',
            name='diff',
            field=models.FloatField(null=True, verbose_name='Разница'),
        ),
        migrations.AlterField(
            model_name='totalpurchases',
            name='month',
            field=models.CharField(max_length=100, null=True, verbose_name='Дата'),
        ),
        migrations.AlterField(
            model_name='totalpurchases',
            name='predicted_total',
            field=models.IntegerField(null=True, verbose_name='Предсказанное количество заказов'),
        ),
        migrations.AlterField(
            model_name='totalpurchases',
            name='real_total',
            field=models.IntegerField(null=True, verbose_name='Реальное количество заказов'),
        ),
    ]
