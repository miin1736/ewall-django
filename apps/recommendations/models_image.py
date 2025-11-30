"""
Image Embedding Model
"""
from django.db import models
from django.contrib.postgres.fields import ArrayField


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
