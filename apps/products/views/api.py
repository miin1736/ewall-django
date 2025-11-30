"""
Product API views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.shortcuts import get_object_or_404
from apps.core.models import Brand, Category
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
)
from apps.products.serializers import ProductListSerializer
from apps.products.services.product_filter import AdvancedProductFilter
import logging

logger = logging.getLogger(__name__)


class ProductListAPIView(APIView):
    """상품 목록 API (Advanced Filtering 지원)
    
    Endpoint: GET /api/products/{brand_slug}/{category_slug}/
    
    Query Parameters:
        # 공통 필터
        - priceMin, priceMax: 가격 범위
        - discountMin, discountMax: 할인율 범위
        - fit: 핏 (regular,slim,oversized - 쉼표 구분 다중 선택)
        - shell: 소재 (nylon,polyester,cotton - 쉼표 구분)
        - inStock: 재고 여부 (true/false)
        - sort: 정렬 (discount,price-low,price-high,newest,popular)
        - page, page_size: 페이지네이션
        
        # 다운 제품 전용
        - downRatio: 다운 비율 (90/10, 80/20, etc.)
        - fillPowerMin, fillPowerMax: 필파워 범위
        - hood: 후드 여부 (true/false)
        - downType: 다운 타입 (duck,goose - 쉼표 구분)
        
        # 슬랙스 전용
        - waistType: 허리 타입 (elastic,button,drawstring)
        - legOpening: 밑단 타입 (straight,tapered,wide)
        - stretch, pleats: boolean
        
        # 청바지 전용
        - wash: 워싱 (light,medium,dark - 쉼표 구분)
        - cut: 컷 (skinny,slim,straight,relaxed,bootcut - 쉼표 구분)
        - rise: 라이즈 (low,mid,high)
        - distressed: boolean
    
    Response:
        {
            "products": [...],
            "total": 150,
            "page": 1,
            "page_size": 20,
            "total_pages": 8,
            "filters_applied": {"downRatio": "90/10", "fillPowerMin": 700},
            "available_filters": {...},
            "price_range": {"min": 50000, "max": 500000},
            "discount_range": {"min": 10, "max": 70}
        }
    """
    
    def get(self, request, brand_slug, category_slug):
        # 필터 서비스 초기화
        filter_service = AdvancedProductFilter(category_slug=category_slug)
        
        # 캐시 키 생성
        cache_key = filter_service.get_filter_cache_key(brand_slug, dict(request.GET))
        
        # 캐시 확인
        cached = filter_service.get_cached_result(cache_key)
        if cached:
            return Response(cached)
        
        # 브랜드, 카테고리 조회
        brand = get_object_or_404(Brand, slug=brand_slug)
        category = get_object_or_404(Category, slug=category_slug)
        
        # 기본 쿼리셋 (브랜드, 재고 있는 상품)
        base_queryset = filter_service.model.objects.filter(
            brand=brand,
            in_stock=True
        )
        
        # 필터링 수행
        queryset, metadata = filter_service.filter(
            base_queryset=base_queryset,
            filters=dict(request.GET),
            optimize=True
        )
        
        # 정렬
        sort = request.GET.get('sort', 'discount')
        queryset = filter_service.sort(queryset, sort)
        
        # 페이지네이션
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        
        total = metadata['count']
        products = queryset[start:start + page_size]
        
        # 직렬화
        serializer = ProductListSerializer(products, many=True)
        
        # 응답 데이터 구성
        response_data = {
            'products': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size,
            'sort': sort,
            
            # 필터 메타데이터 추가
            'filters_applied': metadata['filters_applied'],
            'available_filters': metadata['available_filters'],
            'price_range': metadata['price_range'],
            'discount_range': metadata['discount_range'],
        }
        
        # 캐시 저장 (5분)
        filter_service.set_cached_result(cache_key, response_data, timeout=300)
        
        return Response(response_data)
