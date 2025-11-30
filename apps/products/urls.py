"""
Product API URLs
"""
from django.urls import path
from apps.products.views.api import ProductListAPIView
from apps.products.views.api_price_history import PriceHistoryAPIView
from apps.products.views.api_search import MultiPlatformSearchAPIView, PlatformListAPIView

urlpatterns = [
    path('products/<slug:brand_slug>/<slug:category_slug>/', 
         ProductListAPIView.as_view(), 
         name='product-list'),
    path('products/<str:product_id>/price-history/',
         PriceHistoryAPIView.as_view(),
         name='product-price-history'),
    
    # Multi-platform search
    path('search/',
         MultiPlatformSearchAPIView.as_view(),
         name='multi-platform-search'),
    path('search/platforms/',
         PlatformListAPIView.as_view(),
         name='search-platforms'),
]
