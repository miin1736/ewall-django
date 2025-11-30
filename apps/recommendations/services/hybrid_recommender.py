"""
Hybrid Recommender
"""
from typing import List, Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HybridRecommender:
    """하이브리드 추천 시스템
    
    Features:
        - 협업 필터링 + 인기 기반 결합
        - 가중치 조정 가능
        - 다양성 보장
    """
    
    def __init__(self, cf_weight: float = 0.7, popular_weight: float = 0.3):
        """
        Args:
            cf_weight: 협업 필터링 가중치 (0.0 ~ 1.0)
            popular_weight: 인기 기반 가중치 (0.0 ~ 1.0)
        """
        self.cf_weight = cf_weight
        self.popular_weight = popular_weight
    
    def get_recommendations(
        self,
        product_id: str,
        limit: int = 10,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """하이브리드 추천
        
        Args:
            product_id: 기준 상품 ID
            limit: 반환할 추천 수
            category: 카테고리 필터
            brand: 브랜드 필터
            exclude_ids: 제외할 상품 ID 리스트
        
        Returns:
            추천 상품 리스트
        """
        from apps.recommendations.services.collaborative_filter import CollaborativeFilter
        from apps.recommendations.services.popularity_recommender import PopularityRecommender
        
        exclude_ids = exclude_ids or []
        
        # 협업 필터링 추천
        cf = CollaborativeFilter()
        cf_results = cf.get_recommendations(
            product_id=product_id,
            limit=limit * 2,  # 더 많이 가져와서 다양성 확보
            category=category,
            brand=brand,
            exclude_ids=exclude_ids
        )
        
        # 인기 기반 추천
        popular = PopularityRecommender()
        popular_results = popular.get_popular_products(
            category=category,
            brand=brand,
            limit=limit * 2,
            exclude_ids=exclude_ids
        )
        
        # 점수 결합
        combined_scores = {}
        
        for item in cf_results:
            pid = item['product'].id
            combined_scores[pid] = {
                'product': item['product'],
                'score': item['score'] * self.cf_weight,
                'cf_score': item['score'],
                'popular_score': 0,
                'reason': item['reason']
            }
        
        for item in popular_results:
            pid = item['product'].id
            if pid in combined_scores:
                combined_scores[pid]['score'] += item['score'] * self.popular_weight
                combined_scores[pid]['popular_score'] = item['score']
                combined_scores[pid]['reason'] = 'hybrid'
            else:
                combined_scores[pid] = {
                    'product': item['product'],
                    'score': item['score'] * self.popular_weight,
                    'cf_score': 0,
                    'popular_score': item['score'],
                    'reason': item['reason']
                }
        
        # 점수 순 정렬
        sorted_results = sorted(
            combined_scores.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_results[:limit]
    
    def get_personalized_recommendations(
        self,
        session_id: str,
        limit: int = 10,
        category: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """개인화 추천 (세션 기반)
        
        Args:
            session_id: 사용자 세션 ID
            limit: 반환할 추천 수
            category: 카테고리 필터
            exclude_ids: 제외할 상품 ID 리스트
        
        Returns:
            추천 상품 리스트
        """
        from apps.recommendations.models import UserProductInteraction
        from django.utils import timezone
        from datetime import timedelta
        
        exclude_ids = exclude_ids or []
        
        # 최근 7일 사용자 상호작용
        recent_interactions = UserProductInteraction.objects.filter(
            session_id=session_id,
            created_at__gte=timezone.now() - timedelta(days=7)
        ).order_by('-created_at')[:10]
        
        if not recent_interactions:
            # Cold Start: 인기 상품 반환
            from apps.recommendations.services.popularity_recommender import PopularityRecommender
            popular = PopularityRecommender()
            return popular.get_popular_products(
                category=category,
                limit=limit,
                exclude_ids=exclude_ids
            )
        
        # 상호작용한 상품들에 대한 추천 수집
        all_recommendations = {}
        
        for inter in recent_interactions:
            recommendations = self.get_recommendations(
                product_id=inter.product_id,
                limit=5,
                category=category,
                exclude_ids=exclude_ids + [inter.product_id]
            )
            
            # 가중치 적용 (최근 상호작용일수록 높은 가중치)
            weight = inter.weight
            
            for rec in recommendations:
                pid = rec['product'].id
                if pid not in all_recommendations:
                    all_recommendations[pid] = {
                        'product': rec['product'],
                        'score': 0,
                        'reason': 'personalized'
                    }
                all_recommendations[pid]['score'] += rec['score'] * weight
        
        # 점수 순 정렬
        sorted_results = sorted(
            all_recommendations.values(),
            key=lambda x: x['score'],
            reverse=True
        )
        
        return sorted_results[:limit]
