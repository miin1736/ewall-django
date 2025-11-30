"""
Alert API URLs
"""
from django.urls import path
from apps.alerts.views import AlertCreateAPIView, AlertListAPIView, AlertUpdateAPIView
# from apps.alerts.views.advanced_api import (
#     AlertDashboardAPIView,
#     AlertHistoryAPIView,
#     AlertStatisticsAPIView,
#     AlertConditionValidateAPIView,
#     ProductTrendAPIView,
#     AlertBulkUpdateAPIView,
#     RecommendedAlertsAPIView,
# )

urlpatterns = [
    # 기본 알림 API
    path('alerts/', AlertCreateAPIView.as_view(), name='alert-create'),
    path('alerts/list/', AlertListAPIView.as_view(), name='alert-list'),
    path('alerts/<uuid:alert_id>/', AlertUpdateAPIView.as_view(), name='alert-update'),
    
    # # 고급 알림 API (TODO: Implement advanced_api views)
    # path('alerts/dashboard/', AlertDashboardAPIView.as_view(), name='alert-dashboard'),
    # path('alerts/<uuid:alert_id>/history/', AlertHistoryAPIView.as_view(), name='alert-history'),
    # path('alerts/<uuid:alert_id>/statistics/', AlertStatisticsAPIView.as_view(), name='alert-statistics'),
    # path('alerts/validate-conditions/', AlertConditionValidateAPIView.as_view(), name='alert-validate'),
    # path('alerts/bulk-update/', AlertBulkUpdateAPIView.as_view(), name='alert-bulk-update'),
    # path('alerts/recommended/', RecommendedAlertsAPIView.as_view(), name='alert-recommended'),
    # 
    # # 상품 추세 API
    # path('products/<str:product_id>/trend/', ProductTrendAPIView.as_view(), name='product-trend'),
]
