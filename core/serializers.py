from rest_framework import serializers
from .models import Purchase, Customer


class CustomerSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core:customer-detail")

    class Meta:
        model = Customer
        fields = ('url', 'first_name', 'last_name','recency','recency_cluster','frequency','frequency_cluster',
                  'revenue','revenue_cluster','overall_score','ltv_cluster_prediction','next_purchase_day_range',
                  'segment')


class PurchaseSerializer(serializers.ModelSerializer):
    url = serializers.HyperlinkedIdentityField(view_name="core:purchase-detail")

    class Meta:
        model = Purchase
        fields = ('url', 'title', 'unit_price', 'quantity', 'invoice_date', 'customer', 'invoice_num')
