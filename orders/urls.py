from django.urls import path
from . import views

app_name = 'orders'

urlpatterns = [
    path('checkout/', views.checkout, name='checkout'),
    path('payment/verify/', views.payment_verify, name='payment_verify'),
    path('confirmation/<str:order_number>/', views.order_confirmation, name='order_confirmation'),
    path('payment-failed/<str:order_number>/', views.payment_failed, name='payment_failed'),
    path('tracking/', views.order_tracking, name='tracking'),
    path('order/<str:order_number>/', views.order_detail, name='order_detail'),
    path('reorder/<str:order_number>/', views.reorder, name='reorder'),
]
