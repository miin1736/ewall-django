"""
Recommendation System Tests
"""
import pytest
from django.test import TestCase
from django.utils import timezone
from datetime import timedelta
from apps.recommendations.models import UserProductInteraction, RecommendationCache
from apps.recommendations.services.collaborative_filter import CollaborativeFilter
from apps.recommendations.services.popularity_recommender import PopularityRecommender
from apps.recommendations.services.hybrid_recommender import HybridRecommender


class TestUserProductInteraction(TestCase):
    """UserProductInteraction 모델 테스트"""
    
    def test_create_interaction(self):
        """상호작용 기록 생성"""
        interaction = UserProductInteraction.objects.create(
            session_id='test_session_123',
            product_id='DOWN001',
            product_category='down',
            product_brand='northface',
            interaction_type='view',
            weight=0.5
        )
        
        assert interaction.id is not None
        assert interaction.interaction_type == 'view'
        assert interaction.weight == 0.5
    
    def test_interaction_with_email(self):
        """등록 사용자 상호작용"""
        interaction = UserProductInteraction.objects.create(
            session_id='test_session_456',
            user_email='test@example.com',
            product_id='SLACKS001',
            product_category='slacks',
            product_brand='uniqlo',
            interaction_type='click',
            weight=1.0
        )
        
        assert interaction.user_email == 'test@example.com'
        assert interaction.interaction_type == 'click'


class TestCollaborativeFilter(TestCase):
    """협업 필터링 테스트"""
    
    def setUp(self):
        """테스트 데이터 생성"""
        # 사용자별 상호작용 패턴
        interactions = [
            # User 1: DOWN001, DOWN002, SLACKS001
            ('user1', 'DOWN001', 'down', 'northface', 'view', 0.5),
            ('user1', 'DOWN002', 'down', 'patagonia', 'click', 1.0),
            ('user1', 'SLACKS001', 'slacks', 'uniqlo', 'view', 0.5),
            
            # User 2: DOWN001, DOWN003
            ('user2', 'DOWN001', 'down', 'northface', 'view', 0.5),
            ('user2', 'DOWN003', 'down', 'columbia', 'click', 1.0),
            
            # User 3: DOWN002, SLACKS001, SLACKS002
            ('user3', 'DOWN002', 'down', 'patagonia', 'view', 0.5),
            ('user3', 'SLACKS001', 'slacks', 'uniqlo', 'alert', 1.5),
            ('user3', 'SLACKS002', 'slacks', 'dickies', 'view', 0.5),
        ]
        
        for session_id, product_id, category, brand, inter_type, weight in interactions:
            UserProductInteraction.objects.create(
                session_id=session_id,
                product_id=product_id,
                product_category=category,
                product_brand=brand,
                interaction_type=inter_type,
                weight=weight
            )
    
    def test_build_similarity_matrix(self):
        """유사도 행렬 구축"""
        cf = CollaborativeFilter()
        stats = cf.build_similarity_matrix(days=30, min_interactions=1)
        
        assert 'total_interactions' in stats
        assert stats['total_interactions'] == 8
        assert stats['total_users'] == 3
        assert stats['total_products'] >= 3
    
    def test_recommendation_cache_created(self):
        """추천 캐시 생성 확인"""
        cf = CollaborativeFilter()
        cf.build_similarity_matrix(days=30, min_interactions=1)
        
        caches = RecommendationCache.objects.all()
        assert caches.count() > 0
        
        # 첫 번째 캐시 검증
        cache = caches.first()
        assert cache.algorithm == 'cf'
        assert len(cache.recommended_product_ids) > 0
        assert len(cache.scores) == len(cache.recommended_product_ids)


class TestPopularityRecommender(TestCase):
    """인기 기반 추천 테스트"""
    
    def setUp(self):
        """테스트 데이터 생성"""
        # 다양한 인기도의 상호작용
        products = [
            ('DOWN001', 'down', 'northface', 5),  # 가장 인기
            ('DOWN002', 'down', 'patagonia', 3),
            ('SLACKS001', 'slacks', 'uniqlo', 2),
        ]
        
        for product_id, category, brand, count in products:
            for i in range(count):
                UserProductInteraction.objects.create(
                    session_id=f'user_{i}',
                    product_id=product_id,
                    product_category=category,
                    product_brand=brand,
                    interaction_type='view',
                    weight=0.5
                )
    
    def test_popular_products_basic(self):
        """인기 상품 조회 (기본)"""
        recommender = PopularityRecommender()
        # Note: 실제 Product 모델이 없어서 빈 결과 예상
        results = recommender.get_popular_products(limit=5)
        
        # 구조 검증
        assert isinstance(results, list)
    
    def test_trending_products(self):
        """트렌딩 상품 조회"""
        recommender = PopularityRecommender()
        results = recommender.get_trending_products(hours=24, limit=5)
        
        assert isinstance(results, list)


class TestHybridRecommender(TestCase):
    """하이브리드 추천 테스트"""
    
    def test_hybrid_recommender_init(self):
        """하이브리드 추천 초기화"""
        recommender = HybridRecommender(cf_weight=0.7, popular_weight=0.3)
        
        assert recommender.cf_weight == 0.7
        assert recommender.popular_weight == 0.3
    
    def test_hybrid_recommender_custom_weights(self):
        """커스텀 가중치 설정"""
        recommender = HybridRecommender(cf_weight=0.5, popular_weight=0.5)
        
        assert recommender.cf_weight == 0.5
        assert recommender.popular_weight == 0.5


class TestRecommendationCache(TestCase):
    """추천 캐시 모델 테스트"""
    
    def test_create_cache(self):
        """캐시 생성"""
        cache = RecommendationCache.objects.create(
            product_id='DOWN001',
            recommended_product_ids=['DOWN002', 'DOWN003', 'SLACKS001'],
            scores=[0.85, 0.72, 0.63],
            algorithm='cf',
            metadata={
                'built_at': timezone.now().isoformat(),
                'days': 30,
                'similarity_count': 3
            }
        )
        
        assert cache.product_id == 'DOWN001'
        assert len(cache.recommended_product_ids) == 3
        assert len(cache.scores) == 3
        assert cache.algorithm == 'cf'
    
    def test_cache_update(self):
        """캐시 업데이트"""
        cache = RecommendationCache.objects.create(
            product_id='DOWN002',
            recommended_product_ids=['DOWN001'],
            scores=[0.9],
            algorithm='cf'
        )
        
        # 업데이트
        cache.recommended_product_ids = ['DOWN001', 'DOWN003']
        cache.scores = [0.9, 0.8]
        cache.save()
        
        updated = RecommendationCache.objects.get(product_id='DOWN002')
        assert len(updated.recommended_product_ids) == 2
        assert updated.scores == [0.9, 0.8]


# pytest 실행을 위한 픽스처
@pytest.fixture
def sample_interactions():
    """샘플 상호작용 데이터"""
    interactions = []
    for i in range(10):
        interaction = UserProductInteraction.objects.create(
            session_id=f'session_{i}',
            product_id=f'PRODUCT_{i % 3}',
            product_category='down',
            product_brand='brand',
            interaction_type='view',
            weight=0.5
        )
        interactions.append(interaction)
    return interactions


@pytest.mark.django_db
def test_interaction_filtering(sample_interactions):
    """상호작용 필터링 테스트"""
    # 최근 1일 데이터
    recent = UserProductInteraction.objects.filter(
        created_at__gte=timezone.now() - timedelta(days=1)
    )
    
    assert recent.count() == len(sample_interactions)


@pytest.mark.django_db
def test_product_grouping(sample_interactions):
    """상품별 그룹화 테스트"""
    from django.db.models import Count
    
    grouped = UserProductInteraction.objects.values('product_id').annotate(
        count=Count('id')
    )
    
    # 3개 상품에 고르게 분포
    assert len(grouped) == 3
