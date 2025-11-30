"""
Price History API Views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from django.utils import timezone
from datetime import timedelta
from apps.products.models import (
    PriceHistory, DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
)
from apps.products.serializers_price import PriceChartSerializer
import logging

logger = logging.getLogger(__name__)


class PriceHistoryAPIView(APIView):
    """상품 가격 이력 차트 API
    
    Endpoint: GET /api/products/{product_id}/price-history/
    
    Query Parameters:
        - period: 조회 기간 (7, 30, 90 - 일수, 기본 30)
    
    Response:
        {
            "product_id": "prod_123",
            "product_title": "노스페이스 히말라야 다운",
            "period_days": 30,
            "chart": {
                "labels": ["2025-10-23", "2025-10-24", ...],
                "datasets": [
                    {
                        "label": "가격",
                        "data": [299000, 289000, ...],
                        "borderColor": "rgb(75, 192, 192)",
                        "backgroundColor": "rgba(75, 192, 192, 0.2)"
                    },
                    {
                        "label": "할인율",
                        "data": [50.08, 51.75, ...],
                        "borderColor": "rgb(255, 99, 132)",
                        "backgroundColor": "rgba(255, 99, 132, 0.2)",
                        "yAxisID": "y1"
                    }
                ]
            },
            "stats": {
                "current_price": 289000,
                "lowest_price": 279000,
                "highest_price": 299000,
                "avg_price": 289500,
                "price_change": -10000,
                "price_change_percent": -3.34
            }
        }
    """
    
    def get(self, request, product_id):
        # 기간 파라미터
        period = int(request.GET.get('period', 30))
        if period not in [7, 30, 90]:
            return Response(
                {'error': 'Invalid period. Must be 7, 30, or 90.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 캐시 확인
        cache_key = f"price_history:{product_id}:{period}"
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Cache hit for {cache_key}")
            return Response(cached)
        
        # 상품 조회 (모든 모델에서 검색)
        product = self._get_product(product_id)
        if not product:
            return Response(
                {'error': 'Product not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 가격 이력 조회
        cutoff_date = timezone.now() - timedelta(days=period)
        price_history = PriceHistory.objects.filter(
            product_id=product_id,
            recorded_at__gte=cutoff_date
        ).order_by('recorded_at')
        
        if not price_history.exists():
            return Response(
                {'error': 'No price history available for this period'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 차트 데이터 구성
        labels = []
        price_data = []
        discount_data = []
        
        for record in price_history:
            labels.append(record.recorded_at.strftime('%Y-%m-%d'))
            price_data.append(float(record.price))
            discount_data.append(float(record.discount_rate))
        
        # 통계 계산
        prices = [float(r.price) for r in price_history]
        stats = {
            'current_price': prices[-1] if prices else 0,
            'lowest_price': min(prices) if prices else 0,
            'highest_price': max(prices) if prices else 0,
            'avg_price': sum(prices) / len(prices) if prices else 0,
            'price_change': prices[-1] - prices[0] if len(prices) >= 2 else 0,
            'price_change_percent': ((prices[-1] - prices[0]) / prices[0] * 100) if len(prices) >= 2 and prices[0] > 0 else 0
        }
        
        # Chart.js 형식
        chart_data = {
            'product_id': product_id,
            'product_title': product.title,
            'period_days': period,
            'labels': labels,
            'datasets': [
                {
                    'label': '가격 (원)',
                    'data': price_data,
                    'borderColor': 'rgb(75, 192, 192)',
                    'backgroundColor': 'rgba(75, 192, 192, 0.2)',
                    'yAxisID': 'y',
                    'tension': 0.1
                },
                {
                    'label': '할인율 (%)',
                    'data': discount_data,
                    'borderColor': 'rgb(255, 99, 132)',
                    'backgroundColor': 'rgba(255, 99, 132, 0.2)',
                    'yAxisID': 'y1',
                    'tension': 0.1
                }
            ],
            'stats': stats
        }
        
        # 직렬화
        serializer = PriceChartSerializer(chart_data)
        response_data = serializer.data
        
        # 캐시 저장 (1시간)
        cache.set(cache_key, response_data, timeout=3600)
        
        return Response(response_data)
    
    def _get_product(self, product_id):
        """모든 Product 모델에서 상품 조회"""
        models = [
            DownProduct, SlacksProduct, JeansProduct,
            CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
        ]
        
        for model in models:
            try:
                return model.objects.get(id=product_id)
            except model.DoesNotExist:
                continue
        
        return None
