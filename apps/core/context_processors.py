"""
Context processors for global template variables
"""
from django.core.cache import cache
from apps.core.models import Brand, Category


def sidebar_data(request):
    """모든 템플릿에서 사용할 사이드바 데이터 (캐싱 적용)"""
    cache_key = 'sidebar_data_v1'
    data = cache.get(cache_key)
    
    if data is None:
        data = {
            'all_brands': list(Brand.objects.all().order_by('name')),
            'all_categories': list(Category.objects.all()),
        }
        cache.set(cache_key, data, 3600)  # 1시간 캐싱
    
    return data
