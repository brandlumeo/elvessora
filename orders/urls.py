from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('payment/tamara/success/', views.tamara_success, name='tamara_success'),
    path('payment/tamara/failure/', views.tamara_failure, name='tamara_failure'),
    path('payment/tamara/cancel/', views.tamara_cancel, name='tamara_cancel'),
    path('payment/tamara/webhook/', views.tamara_webhook, name='tamara_webhook'),
    path('payment/tabby/success/', views.tabby_success, name='tabby_success'),
    path('payment/tabby/failure/', views.tabby_failure, name='tabby_failure'),
    path('payment/tabby/cancel/', views.tabby_cancel, name='tabby_cancel'),
    path('payment/tabby/webhook/', views.tabby_webhook, name='tabby_webhook'),
    path('payment/tap/return/', views.tap_return, name='tap_return'),
    path('payment/tap/webhook/', views.tap_webhook, name='tap_webhook'),
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('payment-failed/<str:order_number>/', views.payment_failed, name='payment_failed'),
    path('tracking/', views.order_tracking, name='tracking'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('order/<str:order_number>/invoice/', views.invoice_download, name='invoice_download'),
    path('reorder/<str:order_number>/', views.reorder, name='reorder'),
]
