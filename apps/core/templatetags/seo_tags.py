"""
SEO Template Tags
메타 태그 및 구조화 데이터 템플릿 태그
"""
from django import template
import json

register = template.Library()


@register.inclusion_tag('seo/meta_tags.html')
def render_meta_tags(meta_data):
    """메타 태그 렌더링
    
    Usage:
        {% load seo_tags %}
        {% render_meta_tags meta %}
    
    Args:
        meta_data: SEOMetaGenerator가 생성한 메타 데이터
    """
    return {'meta': meta_data}


@register.inclusion_tag('seo/structured_data.html')
def render_structured_data(*schemas):
    """구조화 데이터 렌더링 (JSON-LD)
    
    Usage:
        {% load seo_tags %}
        {% render_structured_data product_schema breadcrumb_schema %}
    
    Args:
        schemas: StructuredDataGenerator가 생성한 스키마들
    """
    return {'schemas': schemas}


@register.simple_tag
def json_ld(schema):
    """JSON-LD 직접 렌더링
    
    Usage:
        {% load seo_tags %}
        <script type="application/ld+json">
        {% json_ld product_schema %}
        </script>
    """
    return json.dumps(schema, ensure_ascii=False, indent=2)


@register.filter
def truncate_seo(value, length=160):
    """SEO용 텍스트 자르기 (마지막 단어 유지)
    
    Usage:
        {{ description|truncate_seo:160 }}
    """
    if len(value) <= length:
        return value
    
    truncated = value[:length].rsplit(' ', 1)[0]
    return truncated + '...'
