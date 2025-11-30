"""
Recommendation Models
"""
from django.db import models
from django.utils import timezone


class UserProductInteraction(models.Model):
    """사용자-상품 상호작용 기록
    
    협업 필터링을 위한 사용자 행동 데이터 수집
    """
    
    INTERACTION_TYPES = [
        ('view', '조회'),
        ('click', '클릭'),
        ('alert', '알림'),
        ('purchase', '구매'),  # 향후 확장
    ]
    
    session_id = models.CharField(
        max_length=255,
        db_index=True,
        help_text='익명 사용자 세션 ID'
    )
    user_email = models.EmailField(
        null=True,
        blank=True,
        db_index=True,
        help_text='등록 사용자 이메일'
    )
    product_id = models.CharField(
        max_length=50,
        db_index=True,
        help_text='상품 ID'
    )
    product_category = models.CharField(
        max_length=50,
        db_index=True,
        help_text='상품 카테고리'
    )
    product_brand = models.CharField(
        max_length=100,
        help_text='상품 브랜드'
    )
    interaction_type = models.CharField(
        max_length=20,
        choices=INTERACTION_TYPES,
        default='view',
        help_text='상호작용 유형'
    )
    weight = models.FloatField(
        default=1.0,
        help_text='가중치 (view=0.5, click=1.0, alert=1.5, purchase=3.0)'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    
    class Meta:
        db_table = 'user_product_interactions'
        verbose_name = '사용자-상품 상호작용'
        verbose_name_plural = '사용자-상품 상호작용'
        indexes = [
            models.Index(fields=['session_id', 'created_at']),
            models.Index(fields=['product_id', 'interaction_type']),
            models.Index(fields=['product_category', 'created_at']),
        ]
    
    def __str__(self):
        return f"{self.session_id[:8]}... - {self.product_id} ({self.interaction_type})"


class RecommendationCache(models.Model):
    """추천 결과 캐싱
    
    협업 필터링 결과를 미리 계산하여 저장
    """
    
    product_id = models.CharField(
        max_length=50,
        unique=True,
        db_index=True,
        help_text='기준 상품 ID'
    )
    recommended_product_ids = models.JSONField(
        help_text='추천 상품 ID 리스트'
    )
    scores = models.JSONField(
        help_text='추천 점수 리스트'
    )
    algorithm = models.CharField(
        max_length=50,
        help_text='사용된 알고리즘 (cf, popular, hybrid)'
    )
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text='추가 메타데이터 (계산 시간, 샘플 수 등)'
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'recommendation_cache'
        verbose_name = '추천 캐시'
        verbose_name_plural = '추천 캐시'
    
    def __str__(self):
        return f"{self.product_id} - {self.algorithm} ({len(self.recommended_product_ids)} items)"


class ImageEmbedding(models.Model):
    """이미지 임베딩 저장
    
    ResNet50으로 생성된 이미지 벡터 캐싱
    """
    
    product_id = models.CharField(
        max_length=100,
        unique=True,
        db_index=True,
        help_text='상품 ID'
    )
    image_url = models.URLField(
        max_length=2000,
        help_text='원본 이미지 URL'
    )
    embedding_vector = models.JSONField(
        help_text='2048차원 벡터 (JSON array)'
    )
    model_version = models.CharField(
        max_length=50,
        default='resnet50',
        help_text='사용된 모델 버전'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True
    )
    
    class Meta:
        db_table = 'image_embeddings'
        verbose_name = '이미지 임베딩'
        verbose_name_plural = '이미지 임베딩'
        indexes = [
            models.Index(fields=['product_id', 'created_at']),
            models.Index(fields=['model_version', '-created_at']),
        ]
    
    def __str__(self):
        return f"{self.product_id} - {self.model_version}"
