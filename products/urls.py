from django.urls import path
from . import views

app_name = 'products'

urlpatterns = [
    path('collection/', views.collection_landing, name='collection'),
    path('shop/', views.shop, name='shop'),
    path('product/<slug:slug>/', views.product_detail, name='product_detail'),
    path('collections/', views.collection_list, name='collections'),
    path('collections/<slug:slug>/', views.collection_detail, name='collection_detail'),
    path('fragrance-family/<slug:slug>/', views.fragrance_family, name='fragrance_family'),
    path('occasion/<slug:slug>/', views.occasion, name='occasion'),
    path('best-sellers/', views.best_sellers, name='best_sellers'),
    path('new-arrivals/', views.new_arrivals, name='new_arrivals'),
    path('gift-sets/', views.gift_sets, name='gift_sets'),
    path('gift-sets/<slug:slug>/', views.gift_set_detail, name='gift_set_detail'),
]
