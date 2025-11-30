"""Celery 태스크 - 캐시 관리"""
from celery import shared_task
from django.core.cache import cache
from apps.core.models import Brand, Category

@shared_task
def warmup_cache():
    """사이드바 데이터 사전 캐싱"""
    cache_key = 'sidebar_data_v1'
    data = {
        'all_brands': list(Brand.objects.all().order_by('name')),
        'all_categories': list(Category.objects.all()),
    }
    cache.set(cache_key, data, 3600)
    return f"Cache warmed up: {len(data['all_brands'])} brands, {len(data['all_categories'])} categories"
