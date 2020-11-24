# Generated by Django 3.1.1 on 2020-10-06 17:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0005_auto_20200922_0020'),
    ]

    operations = [
        migrations.CreateModel(
            name='Customer',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=50, verbose_name='Имя')),
                ('last_name', models.CharField(max_length=50, verbose_name='Фамилия')),
                ('phone_number', models.CharField(max_length=13, null=True, verbose_name='Номер телефона')),
            ],
            options={
                'verbose_name': 'Сотрудник',
                'verbose_name_plural': 'Сотрудники',
            },
        ),
        migrations.CreateModel(
            name='Purchase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('title', models.CharField(max_length=200)),
                ('unit_price', models.FloatField(verbose_name='Цена за единицу')),
                ('quantity', models.IntegerField(verbose_name='Кол-во товара')),
                ('invoice_date', models.DateTimeField(auto_now_add=True, verbose_name='Дата покупки')),
            ],
        ),
        migrations.DeleteModel(
            name='Employee',
        ),
        migrations.AddField(
            model_name='customer',
            name='purchases',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='core.purchase', verbose_name='Покупки пользователя'),
        ),
    ]
