from django.contrib import admin
from .views import *
from django.urls import path, reverse_lazy, include
from django.contrib.auth.views import LoginView, PasswordResetDoneView, PasswordResetView, PasswordResetConfirmView, \
    PasswordResetCompleteView
from django.conf import settings
from django.conf.urls.static import static
from .dash_apps.finished_apps import simpleexample
from rest_framework import routers

app_name = 'core'
router = routers.DefaultRouter()
router.register('purchases', PurchaseView)
router.register('customers', CustomerView)

urlpatterns = [
    path('accounts/register/done/', RegisterDoneView.as_view(), name='register_done'),
    path('accounts/register/activate/<str:sign>/', user_activate, name='register_activate'),
    path('accounts/register/', RegisterUserView.as_view(), name='register'),
    path('accounts/profile/change_password', BbPasswordChangeView.as_view(), name='password_change'),
    path('accounts/profile/change/', ChangeUserInfoView.as_view(), name='profile_change'),
    path('accounts/profile/', profile, name='profile'),
    path('accounts/logout/', BbLogoutView.as_view(), name='logout'),
    path('accounts/login/', LoginView.as_view(template_name='core/access_control/login.html'), name='login'),
    path('accounts/password_reset/', PasswordResetView.as_view(template_name='core/access_control/reset_password.html',
                                                               subject_template_name='core/access_control/reset_subject.txt',
                                                               email_template_name='core/access_control/reset_email.html',
                                                               success_url=reverse_lazy('core:password_reset_done')),
         name='password_reset'),
    path('accounts/password_reset/done',
         PasswordResetDoneView.as_view(template_name='core/access_control/email_sent.html'),
         name='password_reset_done'),
    path('accounts/reset/<uidb64>/<token>/',
         PasswordResetConfirmView.as_view(template_name='core/access_control/confirm_password.html',
                                          success_url=reverse_lazy('core:password_reset_complete')),
         name='password_reset_confirm'),
    path('accounts/reset/done',
         PasswordResetCompleteView.as_view(template_name='core/access_control/password_confirmed.html'),
         name='password_reset_complete'),
    path('', main_page, name='main_page'),
    path('clients/', tables, name='tables'),
    path('update_elements/', update_elements, name='update_elements'),
    path('graphs/', graphs, name='graphs'),
    path('', include(router.urls)),
    path('customer/<int:customer_id>', customer_detail, name='customer_detail'),
    path('sales/', predict_sales_view, name='predict_sales')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
