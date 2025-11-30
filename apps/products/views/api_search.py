"""
Multi-Platform Search API
여러 쇼핑몰 통합 검색 API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from decimal import Decimal, InvalidOperation
from apps.products.services.search_aggregator import SearchAggregator
import logging

logger = logging.getLogger(__name__)


class MultiPlatformSearchAPIView(APIView):
    """멀티플랫폼 상품 검색 API
    
    GET /api/search/?keyword=노스페이스&platforms=coupang,naver&limit=50
    """
    
    def get(self, request):
        """통합 검색 실행
        
        Query Parameters:
            - keyword (required): 검색 키워드
            - platforms (optional): 검색할 플랫폼 (쉼표 구분, 예: coupang,naver)
            - limit (optional): 플랫폼당 최대 결과 수 (기본 50)
            - min_price (optional): 최소 가격
            - max_price (optional): 최대 가격
            - min_discount (optional): 최소 할인율 (0-100)
            - brand (optional): 브랜드 필터
            - category (optional): 카테고리 필터
        
        Returns:
            {
                'keyword': '노스페이스',
                'total': 100,
                'platforms': {'coupang': 45, 'naver': 55},
                'products': [
                    {
                        'platform': 'coupang',
                        'product_id': '12345',
                        'title': '노스페이스 다운재킷',
                        'price': '89000.00',
                        'original_price': '129000.00',
                        'discount_rate': '31.00',
                        'image_url': 'https://...',
                        'product_url': 'https://...',
                        'seller': '쿠팡',
                        'rating': 4.5,
                        'review_count': 1234,
                        'delivery_info': '로켓배송',
                        'in_stock': True,
                        'brand': '노스페이스',
                        'category': 'down',
                        'score': 75.5
                    },
                    ...
                ],
                'cached': False
            }
        """
        # 필수 파라미터: keyword
        keyword = request.GET.get('keyword')
        if not keyword:
            return Response(
                {'error': 'keyword parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 선택 파라미터
        platforms_param = request.GET.get('platforms')
        platforms = platforms_param.split(',') if platforms_param else None
        
        try:
            limit = int(request.GET.get('limit', 50))
            limit = min(limit, 100)  # 최대 100
        except (ValueError, TypeError):
            limit = 50
        
        # 필터 파라미터
        filters = {}
        
        # 가격 필터
        min_price = request.GET.get('min_price')
        if min_price:
            try:
                filters['min_price'] = int(min_price)  # int로 변환 (Decimal은 내부에서)
            except (ValueError, TypeError):
                pass
        
        max_price = request.GET.get('max_price')
        if max_price:
            try:
                filters['max_price'] = int(max_price)
            except (ValueError, TypeError):
                pass
        
        # 할인율 필터
        min_discount = request.GET.get('min_discount')
        if min_discount:
            try:
                filters['min_discount'] = int(min_discount)
            except (ValueError, TypeError):
                pass
        
        # 브랜드/카테고리 필터
        if request.GET.get('brand'):
            filters['brand'] = request.GET.get('brand')
        
        if request.GET.get('category'):
            filters['category'] = request.GET.get('category')
        
        # 검색 실행
        try:
            aggregator = SearchAggregator()
            result = aggregator.search(
                keyword=keyword,
                platforms=platforms,
                limit=limit,
                **filters
            )
            
            # Decimal을 문자열로 변환 (JSON 직렬화용)
            result = self._serialize_decimals(result)
            
            return Response(result, status=status.HTTP_200_OK)
            
        except Exception as e:
            logger.error(f"Search failed: {e}", exc_info=True)
            return Response(
                {'error': 'Search failed', 'detail': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _serialize_decimals(self, data):
        """Decimal을 문자열로 변환 (재귀)"""
        if isinstance(data, dict):
            return {k: self._serialize_decimals(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._serialize_decimals(item) for item in data]
        elif isinstance(data, Decimal):
            return str(data)
        else:
            return data


class PlatformListAPIView(APIView):
    """사용 가능한 플랫폼 목록 API
    
    GET /api/search/platforms/
    """
    
    def get(self, request):
        """플랫폼 리스트 반환
        
        Returns:
            {
                'platforms': ['coupang', 'naver'],
                'total': 2
            }
        """
        aggregator = SearchAggregator()
        platforms = aggregator.get_available_platforms()
        
        return Response({
            'platforms': platforms,
            'total': len(platforms)
        }, status=status.HTTP_200_OK)
