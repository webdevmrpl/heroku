from django.contrib import admin
from .models import AdvUser, Purchase, Customer, TotalPurchases


# Register your models here.
@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    list_display = ['title', 'unit_price', 'quantity', 'customer', 'invoice_date', 'invoice_num']
    list_display_links = ['title']
    search_fields = ['title','invoice_num']

@admin.register(Customer)
class CustomerAdmin(admin.ModelAdmin):
    list_display = ['first_name', 'last_name']
    search_fields = ['first_name', 'last_name']


admin.site.register(TotalPurchases)
admin.site.register(AdvUser)
