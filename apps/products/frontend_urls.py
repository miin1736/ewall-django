"""
Frontend URLs
"""
from django.urls import path
from apps.products.views.frontend import (
    landing_page, home, product_detail,
    brand_products, category_products
)

urlpatterns = [
    path('', home, name='home'),
    path('products/<str:product_id>/', product_detail, name='product-detail'),
    path('brand/<slug:brand_slug>/', brand_products, name='brand-products'),
    path('category/<slug:category_slug>/', category_products, name='category-products'),
    path('<slug:brand_slug>/<slug:category_slug>/', landing_page, name='landing-page'),
]
