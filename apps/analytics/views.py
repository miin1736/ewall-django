"""
Analytics API views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from apps.analytics.models import Click
from apps.products.models import GenericProduct
import logging

logger = logging.getLogger(__name__)


class OutboundRedirectView(APIView):
    """클릭 트래킹 및 리다이렉트
    
    Endpoint: GET /api/out/?productId={id}&subId={tracking_id}
    """
    
    def get(self, request):
        product_id = request.GET.get('productId')
        sub_id = request.GET.get('subId', '')
        
        if not product_id:
            return Response(
                {'error': 'productId is required'},
                status=400
            )
        
        # GenericProduct에서 상품 조회
        try:
            product = GenericProduct.objects.get(id=product_id)
        except GenericProduct.DoesNotExist:
            return Response(
                {'error': 'Product not found'},
                status=404
            )
        
        # 클릭 기록
        try:
            Click.objects.create(
                product_id=product_id,
                brand=product.brand.name,
                category=product.category.name,
                referrer=request.META.get('HTTP_REFERER'),
                user_agent=request.META.get('HTTP_USER_AGENT'),
            )
            logger.info(f"Click tracked: {product_id}")
        except Exception as e:
            logger.error(f"Failed to track click: {e}")
        
        # 딥링크에 subId 추가
        deeplink = product.deeplink
        if sub_id:
            separator = '&' if '?' in deeplink else '?'
            deeplink = f"{deeplink}{separator}subId={sub_id}"
        
        return HttpResponseRedirect(deeplink)
