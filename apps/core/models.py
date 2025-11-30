"""
Core models: Brand and Category
"""
from django.db import models


class Brand(models.Model):
    """브랜드 모델"""
    name = models.CharField(max_length=100, unique=True, verbose_name='브랜드명')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL 슬러그')
    logo_url = models.URLField(blank=True, null=True, verbose_name='로고 URL')
    description = models.TextField(blank=True, verbose_name='설명')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '브랜드'
        verbose_name_plural = '브랜드'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]
    
    def __str__(self):
        return self.name


class Category(models.Model):
    """카테고리 모델"""
    CATEGORY_CHOICES = [
        ('down', '다운'),
        ('slacks', '슬랙스'),
        ('jeans', '청바지'),
        ('crewneck', '크루넥'),
        ('long-sleeve', '긴팔'),
        ('coat', '코트'),
        ('generic', '기타'),
    ]
    
    name = models.CharField(max_length=100, unique=True, verbose_name='카테고리명')
    slug = models.SlugField(max_length=100, unique=True, verbose_name='URL 슬러그')
    category_type = models.CharField(
        max_length=50, 
        choices=CATEGORY_CHOICES, 
        default='generic',
        verbose_name='카테고리 유형'
    )
    description = models.TextField(blank=True, verbose_name='설명')
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '카테고리'
        verbose_name_plural = '카테고리'
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['category_type']),
        ]
    
    def __str__(self):
        return self.name
