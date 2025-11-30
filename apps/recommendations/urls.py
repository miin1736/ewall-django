"""
Recommendation URL Configuration
"""
from django.urls import path
from apps.recommendations.views.api import (
    ProductRecommendationsAPIView,
    PersonalizedRecommendationsAPIView,
    TrendingProductsAPIView,
    TrackInteractionAPIView
)
from apps.recommendations.views.image_api import (
    SimilarImagesAPIView,
    ImageIndexStatsAPIView,
    GenerateTextureAPIView,
    AvailableProductsAPIView
)
from apps.recommendations.views.image_api_v2 import (
    SimilarImagesV2APIView,
    GenerateTextureV2APIView
)

app_name = 'recommendations'

urlpatterns = [
    # 상품 기반 추천
    path(
        'products/<str:product_id>/',
        ProductRecommendationsAPIView.as_view(),
        name='product_recommendations'
    ),
    
    # 개인화 추천
    path(
        'personalized/',
        PersonalizedRecommendationsAPIView.as_view(),
        name='personalized_recommendations'
    ),
    
    # 트렌딩 상품
    path(
        'trending/',
        TrendingProductsAPIView.as_view(),
        name='trending_products'
    ),
    
    # 상호작용 추적
    path(
        'track/',
        TrackInteractionAPIView.as_view(),
        name='track_interaction'
    ),
    
    # 이미지 유사도 기반 추천
    path(
        'similar-images/<str:product_id>/',
        SimilarImagesAPIView.as_view(),
        name='similar_images'
    ),
    
    # 이미지 인덱스 통계
    path(
        'image-index-stats/',
        ImageIndexStatsAPIView.as_view(),
        name='image_index_stats'
    ),
    
    # AI 질감 이미지 생성
    path(
        'generate-texture/',
        GenerateTextureAPIView.as_view(),
        name='generate_texture'
    ),
    
    # 임베딩이 있는 상품 목록
    path(
        'available-products/',
        AvailableProductsAPIView.as_view(),
        name='available_products'
    ),
    
    # === 개선된 V2 API ===
    # V2: 같은 카테고리 내 비슷한 스타일 추천
    path(
        'v2/similar-images/<str:product_id>/',
        SimilarImagesV2APIView.as_view(),
        name='similar_images_v2'
    ),
    
    # V2: 실제 소재 기반 상세 질감 생성
    path(
        'v2/generate-texture/',
        GenerateTextureV2APIView.as_view(),
        name='generate_texture_v2'
    ),
]
