"""
Collaborative Filtering Recommender
"""
import numpy as np
from collections import defaultdict
from typing import List, Tuple, Dict, Any, Optional
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class CollaborativeFilter:
    """Item-Item 협업 필터링 추천 시스템
    
    Features:
        - Cosine Similarity 기반
        - User-Item 행렬 구축
        - 캐싱 전략
        - Cold Start 해결 (Fallback)
    """
    
    def __init__(self):
        self.similarity_matrix = {}
        self.product_index = {}
    
    def build_similarity_matrix(self, days: int = 30, min_interactions: int = 2) -> Dict[str, Any]:
        """유사도 행렬 구축 (배치 작업)
        
        Args:
            days: 분석할 최근 N일
            min_interactions: 최소 상호작용 수 (필터링)
        
        Returns:
            통계 정보 딕셔너리
        """
        from apps.recommendations.models import UserProductInteraction, RecommendationCache
        
        start_date = timezone.now() - timedelta(days=days)
        
        logger.info(f"Building CF similarity matrix (last {days} days)...")
        
        # 최근 N일 상호작용 데이터
        interactions = UserProductInteraction.objects.filter(
            created_at__gte=start_date
        ).values('session_id', 'product_id', 'weight')
        
        if not interactions:
            logger.warning("No interactions found for building similarity matrix")
            return {'error': 'No interactions found'}
        
        # User-Item 행렬 구축
        user_item_matrix = defaultdict(lambda: defaultdict(float))
        products = set()
        
        for inter in interactions:
            user_item_matrix[inter['session_id']][inter['product_id']] += inter['weight']
            products.add(inter['product_id'])
        
        # 상호작용이 적은 상품 제거
        product_interaction_count = defaultdict(int)
        for user_items in user_item_matrix.values():
            for product_id in user_items.keys():
                product_interaction_count[product_id] += 1
        
        filtered_products = {
            pid for pid, count in product_interaction_count.items()
            if count >= min_interactions
        }
        
        if not filtered_products:
            logger.warning(f"No products with >= {min_interactions} interactions")
            return {'error': f'No products with >= {min_interactions} interactions'}
        
        # 행렬을 numpy로 변환
        product_list = list(filtered_products)
        self.product_index = {pid: idx for idx, pid in enumerate(product_list)}
        
        n_products = len(product_list)
        n_users = len(user_item_matrix)
        item_matrix = np.zeros((n_products, n_users))
        
        for user_idx, (session_id, items) in enumerate(user_item_matrix.items()):
            for product_id, weight in items.items():
                if product_id in self.product_index:
                    product_idx = self.product_index[product_id]
                    item_matrix[product_idx, user_idx] = weight
        
        # Cosine Similarity 계산
        from sklearn.metrics.pairwise import cosine_similarity
        similarity = cosine_similarity(item_matrix)
        
        # 캐시에 저장
        cached_count = 0
        total_recommendations = 0
        
        for i, pid1 in enumerate(product_list):
            similar_items = []
            for j, pid2 in enumerate(product_list):
                if i != j and similarity[i, j] > 0.1:  # 임계값
                    similar_items.append((pid2, float(similarity[i, j])))
            
            # 상위 20개
            similar_items.sort(key=lambda x: x[1], reverse=True)
            similar_items = similar_items[:20]
            
            if similar_items:
                RecommendationCache.objects.update_or_create(
                    product_id=pid1,
                    defaults={
                        'recommended_product_ids': [x[0] for x in similar_items],
                        'scores': [x[1] for x in similar_items],
                        'algorithm': 'cf',
                        'metadata': {
                            'built_at': timezone.now().isoformat(),
                            'days': days,
                            'similarity_count': len(similar_items)
                        }
                    }
                )
                cached_count += 1
                total_recommendations += len(similar_items)
        
        stats = {
            'total_interactions': len(interactions),
            'total_users': n_users,
            'total_products': n_products,
            'cached_products': cached_count,
            'avg_recommendations': round(total_recommendations / cached_count, 2) if cached_count > 0 else 0,
            'days_analyzed': days,
            'completed_at': timezone.now().isoformat()
        }
        
        logger.info(f"CF matrix built: {stats}")
        return stats
    
    def get_recommendations(
        self,
        product_id: str,
        limit: int = 10,
        category: Optional[str] = None,
        brand: Optional[str] = None,
        exclude_ids: Optional[List[str]] = None
    ) -> List[Dict[str, Any]]:
        """추천 상품 조회
        
        Args:
            product_id: 기준 상품 ID
            limit: 반환할 추천 수
            category: 카테고리 필터 (선택)
            brand: 브랜드 필터 (선택)
            exclude_ids: 제외할 상품 ID 리스트
        
        Returns:
            추천 상품 리스트 [{'product': Product, 'score': float, 'reason': str}]
        """
        from apps.recommendations.models import RecommendationCache
        
        exclude_ids = exclude_ids or []
        exclude_ids.append(product_id)  # 자기 자신 제외
        
        # 캐시에서 조회
        try:
            cache = RecommendationCache.objects.get(product_id=product_id)
            recommended_ids = cache.recommended_product_ids[:limit * 2]  # 필터링 고려하여 더 많이
            scores = cache.scores[:limit * 2]
        except RecommendationCache.DoesNotExist:
            # Fallback: 인기 상품
            logger.info(f"No CF cache for product {product_id}, using fallback")
            return self._get_popular_fallback(category, brand, limit)
        
        # 제외 목록 필터링
        filtered_recommendations = [
            (pid, score) for pid, score in zip(recommended_ids, scores)
            if pid not in exclude_ids
        ][:limit]
        
        if not filtered_recommendations:
            return self._get_popular_fallback(category, brand, limit)
        
        # 상품 정보 조회
        from apps.products.models import (
            DownProduct, SlacksProduct, JeansProduct,
            CrewneckProduct, LongSleeveProduct, CoatProduct
        )
        
        models = [DownProduct, SlacksProduct, JeansProduct,
                  CrewneckProduct, LongSleeveProduct, CoatProduct]
        
        # 모든 모델에서 상품 검색
        product_dict = {}
        for model in models:
            products = model.objects.filter(
                id__in=[pid for pid, _ in filtered_recommendations],
                in_stock=True
            )
            
            if category:
                products = products.filter(category__slug=category)
            if brand:
                products = products.filter(brand__slug=brand)
            
            for p in products:
                product_dict[p.id] = p
        
        # 순서 유지하며 결과 구성
        results = []
        for pid, score in filtered_recommendations:
            if pid in product_dict:
                results.append({
                    'product': product_dict[pid],
                    'score': score,
                    'reason': 'similar_products'
                })
        
        # 부족하면 인기 상품으로 채우기
        if len(results) < limit:
            fallback = self._get_popular_fallback(
                category,
                brand,
                limit - len(results)
            )
            results.extend(fallback)
        
        return results[:limit]
    
    def _get_popular_fallback(
        self,
        category: Optional[str],
        brand: Optional[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """인기 상품 Fallback
        
        Args:
            category: 카테고리 슬러그
            brand: 브랜드 슬러그
            limit: 반환 수
        
        Returns:
            인기 상품 리스트
        """
        from apps.recommendations.services.popularity_recommender import PopularityRecommender
        
        recommender = PopularityRecommender()
        return recommender.get_popular_products(
            category=category,
            brand=brand,
            limit=limit
        )
