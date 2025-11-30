"""
Popularity-Based Recommender
"""
from typing import List, Dict, Any, Optional
from django.db.models import Count, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class PopularityRecommender:
    """인기 기반 추천 시스템
    
    Features:
        - Cold Start 문제 해결
        - 카테고리별/브랜드별 인기 상품
        - 할인율 가중치
        - 실시간 조회수 반영
    """
    
    def get_popular_products(
        self,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        limit: int = 10,
        days: int = 7,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """인기 상품 조회
        
        Args:
            category: 카테고리 슬러그
            brand: 브랜드 슬러그
            limit: 반환할 상품 수
            days: 분석할 최근 N일
            exclude_ids: 제외할 상품 ID 리스트
        
        Returns:
            인기 상품 리스트 [{'product': Product, 'score': float, 'reason': str}]
        """
        from apps.recommendations.models import UserProductInteraction
        from apps.products.models import GenericProduct
        
        exclude_ids = exclude_ids or []
        start_date = timezone.now() - timedelta(days=days)
        
        # 최근 N일 인기 상품 (상호작용 기준)
        popular_interactions = UserProductInteraction.objects.filter(
            created_at__gte=start_date
        )
        
        if category:
            popular_interactions = popular_interactions.filter(product_category=category)
        if brand:
            popular_interactions = popular_interactions.filter(product_brand=brand)
        
        # 상품별 점수 계산
        product_scores = {}
        for inter in popular_interactions.values('product_id', 'weight'):
            pid = inter['product_id']
            if pid not in exclude_ids:
                product_scores[pid] = product_scores.get(pid, 0) + inter['weight']
        
        # 상위 N개
        top_product_ids = sorted(
            product_scores.items(),
            key=lambda x: x[1],
            reverse=True
        )[:limit]
        
        if not top_product_ids:
            # Fallback: 전체 인기 상품 (조회수 기준)
            return self._get_view_count_fallback(category, brand, limit, exclude_ids)
        
        # 상품 정보 조회
        queryset = GenericProduct.objects.filter(
            id__in=[pid for pid, _ in top_product_ids],
            in_stock=True
        )
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if brand:
            queryset = queryset.filter(brand__slug=brand)
        
        product_dict = {p.id: p for p in queryset}
        
        # 순서 유지하며 결과 구성
        results = []
        for pid, score in top_product_ids:
            if pid in product_dict:
                results.append({
                    'product': product_dict[pid],
                    'score': float(score),
                    'reason': 'popular'
                })
        
        return results[:limit]
    
    def _get_view_count_fallback(
        self,
        category: Optional[str],
        brand: Optional[str],
        limit: int,
        exclude_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """조회수 기반 Fallback
        
        Args:
            category: 카테고리 슬러그
            brand: 브랜드 슬러그
            limit: 반환 수
            exclude_ids: 제외할 ID 리스트
        
        Returns:
            인기 상품 리스트
        """
        from apps.products.models import GenericProduct
        
        queryset = GenericProduct.objects.filter(
            in_stock=True
        ).exclude(id__in=exclude_ids)
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if brand:
            queryset = queryset.filter(brand__slug=brand)
        
        # 할인율 + 최신순
        products = queryset.order_by('-discount_rate', '-created_at')[:limit]
        
        results = []
        for p in products:
            score = float(p.discount_rate) * 10  # 할인율 기반 점수
            results.append({
                'product': p,
                'score': score,
                'reason': 'popular_discount'
            })
        
        return results
    
    def get_trending_products(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        hours: int = 24
    ) -> List[Dict[str, Any]]:
        """트렌딩 상품 (급상승 인기 상품)
        
        Args:
            category: 카테고리 슬러그
            limit: 반환 수
            hours: 분석할 최근 N시간
        
        Returns:
            트렌딩 상품 리스트
        """
        from apps.recommendations.models import UserProductInteraction
        
        recent_time = timezone.now() - timedelta(hours=hours)
        
        # 최근 N시간 급증한 상품
        trending = UserProductInteraction.objects.filter(
            created_at__gte=recent_time
        )
        
        if category:
            trending = trending.filter(product_category=category)
        
        # 상품별 상호작용 수
        product_counts = trending.values('product_id').annotate(
            count=Count('id')
        ).order_by('-count')[:limit]
        
        if not product_counts:
            return []
        
        # 상품 정보 조회
        from apps.products.models import GenericProduct
        
        product_ids = [item['product_id'] for item in product_counts]
        queryset = GenericProduct.objects.filter(
            id__in=product_ids,
            in_stock=True
        )
        
        if category:
            queryset = queryset.filter(category__slug=category)
        
        product_dict = {p.id: p for p in queryset}
        
        # 결과 구성
        results = []
        for item in product_counts:
            pid = item['product_id']
            if pid in product_dict:
                results.append({
                    'product': product_dict[pid],
                    'score': float(item['count']),
                    'reason': 'trending'
                })
        
        return results[:limit]
