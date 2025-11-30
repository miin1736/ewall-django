"""고트래픽 대응 유틸리티"""
from rest_framework.views import exception_handler
from django.core.cache import cache
from functools import wraps
import hashlib

def custom_exception_handler(exc, context):
    """커스텀 에러 핸들러"""
    response = exception_handler(exc, context)
    if response is not None:
        response.data['status_code'] = response.status_code
    return response

def cache_response(timeout=300, key_prefix='view'):
    """뷰 응답 캐싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            cache_key = f"{key_prefix}:{request.path}:{request.GET.urlencode()}"
            cache_key = hashlib.md5(cache_key.encode()).hexdigest()
            
            cached = cache.get(cache_key)
            if cached:
                return cached
            
            response = func(request, *args, **kwargs)
            
            if request.method == 'GET' and response.status_code == 200:
                cache.set(cache_key, response, timeout)
            
            return response
        return wrapper
    return decorator
