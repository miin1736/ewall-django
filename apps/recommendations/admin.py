"""
Recommendation Admin
"""
from django.contrib import admin
from django.utils.html import format_html
from apps.recommendations.models import UserProductInteraction, RecommendationCache, ImageEmbedding


@admin.register(UserProductInteraction)
class UserProductInteractionAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'session_id_short',
        'product_id',
        'product_category',
        'product_brand',
        'interaction_type',
        'weight',
        'created_at'
    ]
    list_filter = ['interaction_type', 'product_category', 'created_at']
    search_fields = ['session_id', 'user_email', 'product_id']
    date_hierarchy = 'created_at'
    
    def session_id_short(self, obj):
        return f"{obj.session_id[:16]}..."
    session_id_short.short_description = 'Session ID'


@admin.register(RecommendationCache)
class RecommendationCacheAdmin(admin.ModelAdmin):
    list_display = [
        'product_id',
        'algorithm',
        'recommendations_count',
        'updated_at'
    ]
    list_filter = ['algorithm', 'updated_at']
    search_fields = ['product_id']
    readonly_fields = ['updated_at']
    
    def recommendations_count(self, obj):
        return len(obj.recommended_product_ids)
    recommendations_count.short_description = '추천 수'


@admin.register(ImageEmbedding)
class ImageEmbeddingAdmin(admin.ModelAdmin):
    list_display = [
        'product_id',
        'image_thumbnail',
        'model_version',
        'vector_dimension',
        'created_at',
        'updated_at'
    ]
    list_filter = ['model_version', 'created_at']
    search_fields = ['product_id']
    readonly_fields = ['image_preview', 'created_at', 'updated_at']
    
    def image_thumbnail(self, obj):
        """리스트 페이지 썸네일 (작은 크기)"""
        if obj.image_url:
            return format_html(
                '<img src="{}" width="80" height="80" '
                'style="object-fit: cover; border-radius: 4px; border: 1px solid #ddd;" />',
                obj.image_url
            )
        return '-'
    image_thumbnail.short_description = 'IMAGE'
    
    def image_preview(self, obj):
        """상세 페이지 미리보기 (큰 크기)"""
        if obj.image_url:
            return format_html(
                '<div style="margin: 10px 0;">'
                '<img src="{}" style="max-width: 400px; max-height: 400px; '
                'border-radius: 8px; border: 2px solid #ddd; box-shadow: 0 2px 4px rgba(0,0,0,0.1);" />'
                '<p style="margin-top: 10px; color: #666;">이미지 URL: <a href="{}" target="_blank">{}</a></p>'
                '</div>',
                obj.image_url,
                obj.image_url,
                obj.image_url[:100] + '...' if len(obj.image_url) > 100 else obj.image_url
            )
        return '-'
    image_preview.short_description = '이미지 미리보기'
    
    def vector_dimension(self, obj):
        if isinstance(obj.embedding_vector, list):
            return len(obj.embedding_vector)
        return 0
    vector_dimension.short_description = '벡터 차원'
