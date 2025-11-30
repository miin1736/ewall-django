"""
Analytics API URLs
"""
from django.urls import path
from apps.analytics.views import OutboundRedirectView

urlpatterns = [
    path('out/', OutboundRedirectView.as_view(), name='outbound-redirect'),
]
