"""
Advanced Product Filter Service
상품 고급 필터링 및 정렬 서비스

Features:
- 12+ 필터 조건 지원 (down_ratio, fill_power range, hood, fit, shell, price, discount, stock)
- QuerySet 최적화 (select_related, prefetch_related)
- 필터 메타데이터 제공 (available_filters, applied_filters)
- Redis 캐싱 통합
"""
import logging
from typing import Dict, Any, List, Optional, Tuple
from django.db.models import QuerySet, Q, Count, Min, Max
from django.core.cache import cache
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
)

logger = logging.getLogger(__name__)


class AdvancedProductFilter:
    """고급 상품 필터링 서비스
    
    Usage:
        filter_service = AdvancedProductFilter(category_slug='down')
        queryset, metadata = filter_service.filter(
            base_queryset=DownProduct.objects.filter(brand=brand),
            filters={'downRatio': '90/10', 'fillPowerMin': 700, 'hood': True}
        )
    """
    
    # 카테고리별 모델 매핑
    CATEGORY_MODELS = {
        'down': DownProduct,
        'slacks': SlacksProduct,
        'jeans': JeansProduct,
        'crewneck': CrewneckProduct,
        'long-sleeve': LongSleeveProduct,
        'coat': CoatProduct,
        'generic': GenericProduct,
    }
    
    # 정렬 옵션
    SORT_OPTIONS = {
        'discount': '-discount_rate',
        'price-low': 'price',
        'price-high': '-price',
        'newest': '-created_at',
        'popular': '-click_count',  # Click 모델 연동 필요
    }
    
    def __init__(self, category_slug: str):
        """
        Args:
            category_slug: 카테고리 슬러그 (down, slacks, jeans, etc.)
        """
        self.category_slug = category_slug
        self.model = self.CATEGORY_MODELS.get(category_slug, GenericProduct)
    
    def filter(
        self,
        base_queryset: QuerySet,
        filters: Dict[str, Any],
        optimize: bool = True
    ) -> Tuple[QuerySet, Dict[str, Any]]:
        """상품 필터링 수행
        
        Args:
            base_queryset: 기본 쿼리셋 (brand, in_stock 필터 적용된 상태)
            filters: 필터 딕셔너리 (request.GET 또는 dict)
            optimize: QuerySet 최적화 여부
        
        Returns:
            (필터링된 queryset, 메타데이터 dict)
        """
        # 1. 카테고리별 전용 필터 적용
        queryset = self._apply_category_filters(base_queryset, filters)
        
        # 2. 공통 필터 적용
        queryset = self._apply_common_filters(queryset, filters)
        
        # 3. QuerySet 최적화
        if optimize:
            queryset = queryset.select_related('brand', 'category')
        
        # 4. 메타데이터 생성
        metadata = self._generate_metadata(queryset, filters)
        
        return queryset, metadata
    
    def _apply_category_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """카테고리별 전용 필터 적용"""
        
        # QueryDict의 경우 값이 리스트로 올 수 있음 - 첫 번째 값만 사용
        def get_value(key):
            val = filters.get(key)
            if isinstance(val, list):
                return val[0] if val else None
            return val
        
        if self.category_slug == 'down':
            # 다운 제품 필터
            if get_value('downRatio'):
                queryset = queryset.filter(down_ratio=get_value('downRatio'))
            
            if get_value('fillPowerMin'):
                queryset = queryset.filter(fill_power__gte=int(get_value('fillPowerMin')))
            
            if get_value('fillPowerMax'):
                queryset = queryset.filter(fill_power__lte=int(get_value('fillPowerMax')))
            
            if get_value('hood') is not None:
                hood_value = str(get_value('hood')).lower() == 'true'
                queryset = queryset.filter(hood=hood_value)
            
            if get_value('downType'):
                # 여러 개 선택 가능 (쉼표 구분)
                down_type_val = get_value('downType')
                down_types = down_type_val.split(',') if ',' in down_type_val else [down_type_val]
                queryset = queryset.filter(down_type__in=down_types)
        
        elif self.category_slug == 'slacks':
            # 슬랙스 필터
            if get_value('waistType'):
                queryset = queryset.filter(waist_type=get_value('waistType'))
            
            if get_value('legOpening'):
                queryset = queryset.filter(leg_opening=get_value('legOpening'))
            
            if get_value('stretch') is not None:
                stretch_value = str(get_value('stretch')).lower() == 'true'
                queryset = queryset.filter(stretch=stretch_value)
            
            if get_value('pleats') is not None:
                pleats_value = str(get_value('pleats')).lower() == 'true'
                queryset = queryset.filter(pleats=pleats_value)
        
        elif self.category_slug == 'jeans':
            # 청바지 필터
            if get_value('wash'):
                wash_val = get_value('wash')
                washes = wash_val.split(',') if ',' in wash_val else [wash_val]
                queryset = queryset.filter(wash__in=washes)
            
            if get_value('cut'):
                cut_val = get_value('cut')
                cuts = cut_val.split(',') if ',' in cut_val else [cut_val]
                queryset = queryset.filter(cut__in=cuts)
            
            if get_value('rise'):
                queryset = queryset.filter(rise=get_value('rise'))
            
            if get_value('distressed') is not None:
                distressed_value = str(get_value('distressed')).lower() == 'true'
                queryset = queryset.filter(distressed=distressed_value)
        
        elif self.category_slug in ['crewneck', 'long-sleeve']:
            # 상의 필터
            if get_value('neckline'):
                queryset = queryset.filter(neckline=get_value('neckline'))
            
            if get_value('sleeveLength'):
                queryset = queryset.filter(sleeve_length=get_value('sleeveLength'))
            
            if get_value('pattern'):
                pattern_val = get_value('pattern')
                patterns = pattern_val.split(',') if ',' in pattern_val else [pattern_val]
                queryset = queryset.filter(pattern__in=patterns)
        
        elif self.category_slug == 'coat':
            # 코트 필터
            if get_value('length'):
                queryset = queryset.filter(length=get_value('length'))
            
            if get_value('closure'):
                queryset = queryset.filter(closure=get_value('closure'))
            
            if get_value('lining') is not None:
                lining_value = str(get_value('lining')).lower() == 'true'
                queryset = queryset.filter(lining=lining_value)
        
        return queryset
    
    def _apply_common_filters(self, queryset: QuerySet, filters: Dict[str, Any]) -> QuerySet:
        """모든 카테고리 공통 필터 적용"""
        
        # QueryDict의 경우 값이 리스트로 올 수 있음 - 첫 번째 값만 사용
        def get_value(key):
            val = filters.get(key)
            if isinstance(val, list):
                return val[0] if val else None
            return val
        
        # 가격 범위
        if get_value('priceMin'):
            queryset = queryset.filter(price__gte=int(get_value('priceMin')))
        
        if get_value('priceMax'):
            queryset = queryset.filter(price__lte=int(get_value('priceMax')))
        
        # 할인율
        if get_value('discountMin'):
            queryset = queryset.filter(discount_rate__gte=int(get_value('discountMin')))
        
        if get_value('discountMax'):
            queryset = queryset.filter(discount_rate__lte=int(get_value('discountMax')))
        
        # 핏 (여러 개 선택 가능)
        if get_value('fit'):
            fit_val = get_value('fit')
            fits = fit_val.split(',') if ',' in fit_val else [fit_val]
            queryset = queryset.filter(fit__in=fits)
        
        # 소재 (여러 개 선택 가능)
        if get_value('shell'):
            shell_val = get_value('shell')
            shells = shell_val.split(',') if ',' in shell_val else [shell_val]
            queryset = queryset.filter(shell__in=shells)
        
        # 재고 여부
        if get_value('inStock') is not None:
            stock_value = str(get_value('inStock')).lower() == 'true'
            queryset = queryset.filter(in_stock=stock_value)
        
        # 색상 (추후 Color 모델 연동 시)
        if get_value('color'):
            color_val = get_value('color')
            colors = color_val.split(',') if ',' in color_val else [color_val]
            queryset = queryset.filter(color__in=colors)
        
        # 사이즈 (추후 Size 모델 연동 시)
        if get_value('size'):
            size_val = get_value('size')
            sizes = size_val.split(',') if ',' in size_val else [size_val]
            queryset = queryset.filter(sizes__name__in=sizes)
        
        return queryset
    
    def _generate_metadata(self, queryset: QuerySet, filters: Dict[str, Any]) -> Dict[str, Any]:
        """필터 메타데이터 생성
        
        Returns:
            {
                'filters_applied': {...},  # 적용된 필터
                'available_filters': {...},  # 사용 가능한 필터 옵션 (동적)
                'count': int,  # 필터 결과 개수
                'price_range': {'min': int, 'max': int},
                'discount_range': {'min': int, 'max': int}
            }
        """
        metadata = {
            'filters_applied': self._clean_filters(filters),
            'count': queryset.count(),
        }
        
        # 가격 범위 (현재 필터 결과 기준)
        price_stats = queryset.aggregate(
            min_price=Min('price'),
            max_price=Max('price')
        )
        metadata['price_range'] = {
            'min': price_stats['min_price'] or 0,
            'max': price_stats['max_price'] or 0
        }
        
        # 할인율 범위
        discount_stats = queryset.aggregate(
            min_discount=Min('discount_rate'),
            max_discount=Max('discount_rate')
        )
        metadata['discount_range'] = {
            'min': discount_stats['min_discount'] or 0,
            'max': discount_stats['max_discount'] or 0
        }
        
        # 사용 가능한 필터 옵션 (카테고리별)
        metadata['available_filters'] = self._get_available_filters(queryset)
        
        return metadata
    
    def _clean_filters(self, filters: Dict[str, Any]) -> Dict[str, Any]:
        """적용된 필터만 반환 (빈 값 제외), 리스트는 첫 번째 값만"""
        cleaned = {}
        for k, v in filters.items():
            if v not in [None, '', []]:
                # QueryDict의 경우 리스트로 올 수 있음
                if isinstance(v, list):
                    cleaned[k] = v[0] if v else None
                else:
                    cleaned[k] = v
        return {k: v for k, v in cleaned.items() if v is not None}
    
    def _get_available_filters(self, queryset: QuerySet) -> Dict[str, Any]:
        """현재 쿼리셋에서 사용 가능한 필터 옵션 반환
        
        예: 노스페이스 다운 카테고리라면 실제로 존재하는 down_ratio, fill_power 값들만 반환
        """
        available = {}
        
        if self.category_slug == 'down':
            # 다운비율 옵션
            available['downRatio'] = list(
                queryset.values_list('down_ratio', flat=True).distinct()
            )
            
            # 필파워 범위
            fill_power_stats = queryset.aggregate(
                min_fp=Min('fill_power'),
                max_fp=Max('fill_power')
            )
            available['fillPower'] = {
                'min': fill_power_stats['min_fp'],
                'max': fill_power_stats['max_fp']
            }
            
            # 다운 타입
            available['downType'] = list(
                queryset.values_list('down_type', flat=True).distinct()
            )
            
            # 후드 여부
            available['hood'] = queryset.filter(hood=True).exists()
        
        elif self.category_slug == 'slacks':
            available['waistType'] = list(
                queryset.values_list('waist_type', flat=True).distinct()
            )
            available['legOpening'] = list(
                queryset.values_list('leg_opening', flat=True).distinct()
            )
        
        elif self.category_slug == 'jeans':
            available['wash'] = list(
                queryset.values_list('wash', flat=True).distinct()
            )
            available['cut'] = list(
                queryset.values_list('cut', flat=True).distinct()
            )
            available['rise'] = list(
                queryset.values_list('rise', flat=True).distinct()
            )
        
        # 공통 필터
        available['fit'] = list(
            queryset.values_list('fit', flat=True).distinct()
        )
        available['shell'] = list(
            queryset.values_list('shell', flat=True).distinct()
        )
        
        return available
    
    def sort(self, queryset: QuerySet, sort_key: str = 'discount') -> QuerySet:
        """쿼리셋 정렬
        
        Args:
            queryset: 정렬할 쿼리셋
            sort_key: 정렬 키 (discount, price-low, price-high, newest, popular)
        
        Returns:
            정렬된 쿼리셋
        """
        order_by = self.SORT_OPTIONS.get(sort_key, '-discount_rate')
        return queryset.order_by(order_by)
    
    def get_filter_cache_key(self, brand_slug: str, filters: Dict[str, Any]) -> str:
        """필터 캐시 키 생성
        
        Args:
            brand_slug: 브랜드 슬러그
            filters: 필터 딕셔너리
        
        Returns:
            Redis 캐시 키 (예: "filter:northface:down:downRatio=90/10&fillPowerMin=700")
        """
        # 필터를 정렬하여 일관된 캐시 키 생성
        sorted_filters = sorted(self._clean_filters(filters).items())
        filter_string = '&'.join([f"{k}={v}" for k, v in sorted_filters])
        
        return f"filter:{brand_slug}:{self.category_slug}:{filter_string}"
    
    def get_cached_result(self, cache_key: str) -> Optional[Dict[str, Any]]:
        """캐시된 필터 결과 가져오기
        
        Args:
            cache_key: 캐시 키
        
        Returns:
            캐시된 데이터 또는 None
        """
        cached = cache.get(cache_key)
        if cached:
            logger.info(f"Filter cache hit: {cache_key}")
        return cached
    
    def set_cached_result(self, cache_key: str, data: Dict[str, Any], timeout: int = 300):
        """필터 결과 캐싱
        
        Args:
            cache_key: 캐시 키
            data: 캐시할 데이터
            timeout: 캐시 유효 시간 (초, 기본 5분)
        """
        cache.set(cache_key, data, timeout=timeout)
        logger.info(f"Filter result cached: {cache_key}")
