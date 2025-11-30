"""
AI/ML 기반 카테고리 자동 분류 서비스
ResNet50 이미지 임베딩을 활용한 유사도 기반 분류
"""
import numpy as np
from typing import Optional, List, Tuple
from django.db.models import Q
from apps.recommendations.models import ImageEmbedding
from apps.products.models import GenericProduct
from apps.core.models import Category
import logging

logger = logging.getLogger(__name__)


class CategoryClassifier:
    """이미지 임베딩 기반 카테고리 분류기"""
    
    def __init__(self):
        self.embedding_cache = {}
        self.category_cache = {}
    
    def classify_product(self, product_or_image_url: str, title: str = '') -> str:
        """
        상품을 자동으로 카테고리에 분류
        
        Args:
            product_or_image_url: GenericProduct ID 또는 이미지 URL
            title: 상품명 (폴백용)
        
        Returns:
            카테고리 slug (down, coat, jeans 등)
        """
        # 1단계: 이미지 임베딩 기반 분류 시도
        category = self._classify_by_embedding(product_or_image_url)
        if category != 'generic':
            logger.info(f"✅ AI 분류 성공: {category}")
            return category
        
        # 2단계: 텍스트 키워드 폴백
        if title:
            category = self._classify_by_keywords(title)
            logger.info(f"⚠️ 키워드 폴백: {category}")
            return category
        
        logger.warning(f"❌ 분류 실패 → generic")
        return 'generic'
    
    def _classify_by_embedding(self, product_id: str) -> str:
        """이미지 임베딩 기반 분류 (KNN 방식)"""
        try:
            # 해당 상품의 임베딩 가져오기
            target_embedding = ImageEmbedding.objects.filter(
                product_id=product_id,
                model_version='resnet50'
            ).first()
            
            if not target_embedding:
                logger.debug(f"임베딩 없음: {product_id}")
                return 'generic'
            
            target_vector = np.array(target_embedding.embedding_vector, dtype=np.float32)
            
            # 카테고리별 대표 상품들의 임베딩 가져오기 (K=5)
            category_scores = {}
            
            for category_slug in ['down', 'coat', 'jeans', 'slacks', 'crewneck', 'long-sleeve']:
                # 해당 카테고리의 상품 중 임베딩 있는 것들
                category_products = GenericProduct.objects.filter(
                    category__slug=category_slug,
                    in_stock=True
                ).values_list('id', flat=True)[:50]  # 최대 50개
                
                embeddings = ImageEmbedding.objects.filter(
                    product_id__in=category_products,
                    model_version='resnet50'
                )
                
                if not embeddings.exists():
                    continue
                
                # 코사인 유사도 계산
                similarities = []
                for emb in embeddings[:10]:  # 최대 10개와 비교
                    ref_vector = np.array(emb.embedding_vector, dtype=np.float32)
                    similarity = self._cosine_similarity(target_vector, ref_vector)
                    similarities.append(similarity)
                
                # 평균 유사도
                if similarities:
                    category_scores[category_slug] = np.mean(similarities)
            
            # 가장 유사한 카테고리 선택 (임계값 0.35)
            if category_scores:
                best_category = max(category_scores, key=category_scores.get)
                best_score = category_scores[best_category]
                
                logger.info(f"유사도 점수: {category_scores}")
                
                if best_score >= 0.35:  # 임계값: 0.35로 조정 (기존 0.7)
                    return best_category
            
            return 'generic'
            
        except Exception as e:
            logger.error(f"임베딩 분류 실패: {e}")
            return 'generic'
    
    def _classify_by_keywords(self, title: str) -> str:
        """텍스트 키워드 기반 분류 (폴백)"""
        title_lower = title.lower()
        
        # 키워드 우선순위 매칭
        keyword_rules = [
            (['패딩', '다운점퍼', '덕다운', '구스다운', '눕시'], 'down'),
            (['슬랙스', '정장바지'], 'slacks'),
            (['청바지', '데님', '진팬츠'], 'jeans'),
            (['맨투맨', '크루넥', '스웨트셔츠'], 'crewneck'),
            (['긴팔', '롱슬리브', '긴팔티'], 'long-sleeve'),
            (['코트', '자켓', '점퍼', '잠바'], 'coat'),
        ]
        
        for keywords, category in keyword_rules:
            if any(kw in title_lower for kw in keywords):
                return category
        
        return 'generic'
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """코사인 유사도 계산"""
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return np.dot(vec1, vec2) / (norm1 * norm2)
    
    def batch_classify(self, product_ids: List[str]) -> dict:
        """여러 상품을 한번에 분류
        
        Returns:
            {product_id: category_slug}
        """
        results = {}
        
        for pid in product_ids:
            try:
                product = GenericProduct.objects.get(id=pid)
                category = self.classify_product(pid, product.title)
                results[pid] = category
            except GenericProduct.DoesNotExist:
                results[pid] = 'generic'
        
        return results


def get_classifier() -> CategoryClassifier:
    """싱글톤 분류기 인스턴스 반환"""
    if not hasattr(get_classifier, '_instance'):
        get_classifier._instance = CategoryClassifier()
    return get_classifier._instance
