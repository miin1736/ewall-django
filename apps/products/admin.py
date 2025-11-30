"""
Product admin
"""
from django.contrib import admin
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct,
    PriceHistory
)


@admin.register(DownProduct)
class DownProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock', 'created_at']
    list_filter = ['brand', 'in_stock', 'down_type', 'down_ratio']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']
    list_per_page = 50
    
    fieldsets = (
        ('기본 정보', {
            'fields': ('id', 'brand', 'category', 'title', 'slug', 'image_url')
        }),
        ('가격 정보', {
            'fields': ('price', 'original_price', 'discount_rate', 'currency')
        }),
        ('판매 정보', {
            'fields': ('seller', 'deeplink', 'in_stock', 'score', 'source')
        }),
        ('다운 속성', {
            'fields': ('down_type', 'down_ratio', 'fill_power', 'hood', 'fit', 'shell', 'material_composition')
        }),
        ('메타', {
            'fields': ('created_at', 'updated_at')
        }),
    )


@admin.register(SlacksProduct)
class SlacksProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock']
    list_filter = ['brand', 'in_stock', 'waist_type', 'leg_opening']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(JeansProduct)
class JeansProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock']
    list_filter = ['brand', 'in_stock', 'wash', 'cut']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CrewneckProduct)
class CrewneckProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock']
    list_filter = ['brand', 'in_stock', 'neckline', 'pattern']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(LongSleeveProduct)
class LongSleeveProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock']
    list_filter = ['brand', 'in_stock']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(CoatProduct)
class CoatProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock']
    list_filter = ['brand', 'in_stock', 'length', 'closure']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(GenericProduct)
class GenericProductAdmin(admin.ModelAdmin):
    list_display = ['title', 'brand', 'category', 'price', 'discount_rate', 'material_composition', 'in_stock']
    list_filter = ['brand', 'in_stock']
    search_fields = ['title', 'id', 'material_composition']
    readonly_fields = ['id', 'created_at', 'updated_at']


@admin.register(PriceHistory)
class PriceHistoryAdmin(admin.ModelAdmin):
    list_display = ['product_id', 'product_type', 'price', 'discount_rate', 'recorded_at']
    list_filter = ['product_type', 'recorded_at']
    search_fields = ['product_id']
    readonly_fields = ['product_id', 'product_type', 'price', 'original_price', 'discount_rate', 'recorded_at']
    date_hierarchy = 'recorded_at'
    list_per_page = 100
    
    def has_add_permission(self, request):
        # Celery Task에서만 추가하므로 Admin에서는 추가 불가
        return False
    
    def has_delete_permission(self, request, obj=None):
        # 관리자만 삭제 가능 (데이터 정리용)
        return request.user.is_superuser
