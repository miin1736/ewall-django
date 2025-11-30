"""
URL configuration for E-wall project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.contrib.sitemaps.views import sitemap
from django.views.generic import TemplateView
from apps.products.sitemaps import (
    LandingPageSitemap,
    ProductDetailSitemap,
    ProductImageSitemap
)
from drf_spectacular.views import (
    SpectacularAPIView,
    SpectacularSwaggerView,
    SpectacularRedocView
)

sitemaps = {
    'landing': LandingPageSitemap,
    'products': ProductDetailSitemap,
    'images': ProductImageSitemap,
}

urlpatterns = [
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    
    # API endpoints
    path('api/', include('apps.products.urls')),
    path('api/', include('apps.alerts.urls')),
    path('api/', include('apps.analytics.urls')),
    path('api/recommendations/', include('apps.recommendations.urls')),
    
    # SEO files
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt', 
        content_type='text/plain'
    ), name='robots'),
    
    # Frontend (landing pages)
    path('', include('apps.products.frontend_urls')),
]

# Serve media files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    
    # Django Debug Toolbar
    try:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include('debug_toolbar.urls')),
        ] + urlpatterns
    except ImportError:
        pass

# Admin site customization
admin.site.site_header = "E-wall 관리자"
admin.site.site_title = "E-wall Admin"
admin.site.index_title = "대시보드"
