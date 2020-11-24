from django.contrib.auth.models import AbstractUser
from django.db import models
from .utilities import send_activation_notification
from django.dispatch import Signal, receiver


class Purchase(models.Model):
    title = models.CharField(max_length=200, verbose_name='Название товара')
    unit_price = models.FloatField(verbose_name='Цена за единицу')
    quantity = models.IntegerField(verbose_name='Кол-во товара')
    invoice_date = models.DateTimeField(verbose_name='Дата покупки')
    customer = models.ForeignKey('Customer', on_delete=models.PROTECT, verbose_name='Покупатель', related_name='second')
    invoice_num = models.IntegerField(verbose_name='Номер заказа', null=True)

    class Meta:
        verbose_name = 'Покупка'
        verbose_name_plural = 'Покупки'

    def __str__(self):
        return self.title


class Customer(models.Model):
    first_name = models.CharField(max_length=50, verbose_name='Имя', null=True, blank=True)
    last_name = models.CharField(max_length=50, verbose_name='Фамилия', null=True, blank=True)
    recency = models.IntegerField(null=True, blank=True)
    recency_cluster = models.IntegerField(blank=True, null=True)
    frequency = models.IntegerField(blank=True, null=True)
    frequency_cluster = models.IntegerField(blank=True, null=True)
    revenue = models.IntegerField(blank=True, null=True)
    revenue_cluster = models.IntegerField(blank=True, null=True)
    overall_score = models.IntegerField(blank=True, null=True)
    ltv_cluster_prediction = models.IntegerField(blank=True, null=True)
    next_purchase_day_range = models.IntegerField(blank=True, null=True)
    segment = models.CharField(max_length=30, blank=True, null=True)

    class Meta:
        verbose_name = 'Покупатель'
        verbose_name_plural = 'Покупатели'

    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class AdvUser(AbstractUser):
    is_activated = models.BooleanField(default=True, verbose_name='Пройдена ли активация?')
    company_name = models.CharField(max_length=200, verbose_name='Название компании')

    class Meta(AbstractUser.Meta):
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


user_registered = Signal(providing_args=['instance'])


@receiver(user_registered)
def user_registered_dispatcher(sender, **kwargs):
    send_activation_notification(kwargs['instance'])


class TotalPurchases(models.Model):
    month = models.CharField(max_length=100, verbose_name='Дата',null=True, unique=True)
    real_total = models.IntegerField(verbose_name='Реальное количество заказов',null=True)
    predicted_total = models.IntegerField(verbose_name='Предсказанное количество заказов',null=True)
    diff = models.FloatField(verbose_name='Разница',null=True)