"""
Click tracking model
"""
import uuid
from django.db import models


class Click(models.Model):
    """클릭 추적 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    product_id = models.CharField(max_length=100, db_index=True, verbose_name='상품 ID')
    brand = models.CharField(max_length=100, verbose_name='브랜드')
    category = models.CharField(max_length=50, verbose_name='카테고리')
    
    referrer = models.CharField(max_length=200, null=True, blank=True, verbose_name='유입 경로')
    user_agent = models.CharField(max_length=500, null=True, blank=True, verbose_name='사용자 에이전트')
    
    timestamp = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='클릭 시각')
    
    class Meta:
        verbose_name = '클릭 추적'
        verbose_name_plural = '클릭 추적'
        indexes = [
            models.Index(fields=['timestamp']),
            models.Index(fields=['product_id', 'timestamp']),
            models.Index(fields=['brand', 'category', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.brand} - {self.category} - {self.timestamp}"


class DailyClickAggregate(models.Model):
    """일일 클릭 집계 모델"""
    date = models.DateField(db_index=True, verbose_name='날짜')
    brand = models.CharField(max_length=100, verbose_name='브랜드')
    category = models.CharField(max_length=50, verbose_name='카테고리')
    
    click_count = models.IntegerField(default=0, verbose_name='클릭 수')
    unique_products = models.IntegerField(default=0, verbose_name='고유 상품 수')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '일일 클릭 집계'
        verbose_name_plural = '일일 클릭 집계'
        unique_together = [['date', 'brand', 'category']]
        indexes = [
            models.Index(fields=['date', 'brand', 'category']),
        ]
    
    def __str__(self):
        return f"{self.date} - {self.brand} {self.category}: {self.click_count}"
