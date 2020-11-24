from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.views import LogoutView, PasswordChangeView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.signing import BadSignature
from django.http import HttpResponseRedirect
from django.shortcuts import render, get_object_or_404
from .forms import RegisterUserForm, ChangeUserInfoForm
from .utilities import signer
from django.urls import reverse_lazy, reverse
from django.views.generic import UpdateView, CreateView, TemplateView
from .models import AdvUser, Customer, Purchase, TotalPurchases
from .complete_script import make_predictions, predict_sales
import pandas as pd
from datetime import datetime
from .graphs_data import *
from .serializers import PurchaseSerializer, CustomerSerializer
from rest_framework import viewsets
from .cards import *
from django.views.decorators.cache import cache_page


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
# ACCESS CONTROL SETTINGS
class BbLogoutView(LoginRequiredMixin, LogoutView):
    template_name = 'core/access_control/logout.html'


@login_required
def profile(request):
    return render(request, 'core/access_control/profile.html')


def tables(request):
    customers = Customer.objects.all()
    return render(request, 'core/main_html/tables.html', {'customers': customers})


class ChangeUserInfoView(SuccessMessageMixin, LoginRequiredMixin, UpdateView):
    model = AdvUser
    template_name = 'core/access_control/change_user_info.html'
    form_class = ChangeUserInfoForm
    success_url = reverse_lazy('core:profile')
    success_message = 'Личные данные пользователя изменены'

    def dispatch(self, request, *args, **kwargs):
        self.user_id = request.user.pk
        return super().dispatch(request, *args, **kwargs)

    def get_object(self, queryset=None):
        if not queryset:
            queryset = self.get_queryset()
        return get_object_or_404(queryset, pk=self.user_id)


class BbPasswordChangeView(LoginRequiredMixin, SuccessMessageMixin, PasswordChangeView):
    template_name = 'core/access_control/change_password.html'
    success_url = reverse_lazy('core:profile')
    success_message = 'Пароль успешно изменен'


class RegisterUserView(CreateView):
    model = AdvUser
    template_name = 'core/access_control/register_form.html'
    form_class = RegisterUserForm
    success_url = reverse_lazy('core:register_done')


class RegisterDoneView(TemplateView):
    template_name = 'core/access_control/register_done.html'


def user_activate(request, sign):
    try:
        username = signer.unsign(sign)
    except BadSignature:
        return render(request, 'core/access_control/bad_signature.html')
    user = get_object_or_404(AdvUser, username=username)
    if user.is_activated:
        template = 'core/access_control/user_is_activated.html'
    else:
        template = 'core/access_control/activation_done.html'
        user.is_active = True
        user.is_activated = True
        user.save()
    return render(request, template)


# //////////////////////////////////////////////////////////////////////////////////////////////////////////////////////

@cache_page(21600, cache='default')
def main_page(request):
    customers = Customer.objects.all()
    customer_count = len(Customer.objects.all())
    monthly_revenue_first = monthly_revenue_card()
    monthly_revenue_exit = '{:,}'.format(monthly_revenue_first).replace(',', ' ')
    progress = int((monthly_revenue_first / 2000000) * 100)
    return render(request, 'core/main_html/index.html',
                  {'customers': customers, 'monthly_revenue_card': monthly_revenue_exit,
                   'annual_revenue': annual_revenue_card(),
                   'customer_count': customer_count,
                   'progress': progress,
                   'monthly_revenue_graph': monthly_revenue_scatter_mainpage(),
                   'monthly_active_users': monthly_active_customers_pie()})


@cache_page(43200, cache='default')
def graphs(request):
    return render(request, 'core/main_html/graphs.html', {'monthly_revenue': monthly_revenue_scatter(),
                                                          'monthly_growth': monthly_growth_scatter(),
                                                          'monthly_active_customers': monthly_active_customers_scatter(),
                                                          'total_purchased_items': total_purchased_items_scatter(),
                                                          'monthly_order_average': monthly_order_average_scatter(),
                                                          'new_vs_existing': new_vs_existing_scatter(),
                                                          'new_customer_ratio': new_customer_ratio_scatter(),
                                                          'monthly_retention_rate': monthly_retention_rate_scatter()
                                                          })


def assign_elements(customer, df):
    for i in customer:
        dff = df.loc[df['CustomerID'] == i.pk]
        if dff.empty:
            continue
        i.recency = list(dff.Recency)[0]
        i.recency_cluster = list(dff.RecencyCluster)[0]
        i.frequency = list(dff.Frequency)[0]
        i.frequency_cluster = list(dff.FrequencyCluster)[0]
        i.revenue = list(dff.Revenue)[0]
        i.revenue_cluster = list(dff.RevenueCluster)[0]
        i.overall_score = list(dff.OverallScore)[0]
        i.ltv_cluster_prediction = list(dff.LTVClusterPrediction)[0]
        i.next_purchase_day_range = list(dff.NextPurchaseDayRange)[0]
        i.segment = list(dff.Segment)[0]
        i.save()


def update_elements(request):
    customers = Customer.objects.filter(second__isnull=False).distinct()
    df = pd.DataFrame(list(Purchase.objects.all().values()))
    df = df.drop('id', axis=1)
    df.columns = ['Description', 'UnitPrice', 'Quantity', 'InvoiceDate', 'CustomerID', 'InvoiceNo']
    df = make_predictions(df)
    assign_elements(customers, df)
    return HttpResponseRedirect(reverse('core:tables'))


class PurchaseView(viewsets.ModelViewSet):
    queryset = Purchase.objects.all()
    serializer_class = PurchaseSerializer


class CustomerView(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer


def customer_detail(request, customer_id):
    customer = Customer.objects.get(pk=customer_id).second.all()
    return render(request, 'core/main_html/customer_buys.html', {'customer': customer})


def predict_sales_view(request):
    df_sales = pd.DataFrame(list(Purchase.objects.all().values()))
    ready_df = predict_sales(df_sales)
    for i in ready_df.itertuples():
        k = TotalPurchases.objects.get_or_create(month=i.date)[0]
        k.real_total = i.sales
        k.predicted_total = i.pred_value
        k.diff = i.diff
        k.save()
    done = TotalPurchases.objects.all()
    return render(request, 'core/main_html/purchases.html', {'purchases':done})
