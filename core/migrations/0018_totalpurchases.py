# Generated by Django 3.1.1 on 2020-11-21 22:56

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0017_auto_20201027_1753'),
    ]

    operations = [
        migrations.CreateModel(
            name='TotalPurchases',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('month', models.CharField(max_length=100, verbose_name='Дата')),
                ('real_total', models.IntegerField(verbose_name='Реальное количество заказов')),
                ('predicted_total', models.IntegerField(verbose_name='Предсказанное количество заказов')),
            ],
        ),
    ]
