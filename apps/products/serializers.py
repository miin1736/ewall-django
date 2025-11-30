"""
Product serializers
"""
from rest_framework import serializers
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
)


class ProductListSerializer(serializers.Serializer):
    """상품 목록 직렬화 (모든 카테고리 공통)"""
    id = serializers.CharField()
    brand_name = serializers.CharField(source='brand.name')
    category_name = serializers.CharField(source='category.name')
    
    title = serializers.CharField()
    slug = serializers.SlugField()
    image_url = serializers.URLField()
    
    price = serializers.DecimalField(max_digits=10, decimal_places=0)
    original_price = serializers.DecimalField(max_digits=10, decimal_places=0)
    discount_rate = serializers.DecimalField(max_digits=5, decimal_places=2)
    
    in_stock = serializers.BooleanField()
    score = serializers.FloatField()
    
    # 카테고리별 속성 (동적으로 포함)
    down_type = serializers.CharField(required=False, allow_null=True)
    down_ratio = serializers.CharField(required=False, allow_null=True)
    fill_power = serializers.IntegerField(required=False, allow_null=True)
    hood = serializers.BooleanField(required=False, allow_null=True)
    
    waist_type = serializers.CharField(required=False, allow_null=True)
    leg_opening = serializers.CharField(required=False, allow_null=True)
    stretch = serializers.BooleanField(required=False, allow_null=True)
    pleats = serializers.CharField(required=False, allow_null=True)
    
    wash = serializers.CharField(required=False, allow_null=True)
    cut = serializers.CharField(required=False, allow_null=True)
    rise = serializers.CharField(required=False, allow_null=True)
    distressed = serializers.BooleanField(required=False, allow_null=True)
    
    neckline = serializers.CharField(required=False, allow_null=True)
    sleeve_length = serializers.CharField(required=False, allow_null=True)
    pattern = serializers.CharField(required=False, allow_null=True)
    
    fit = serializers.CharField(required=False, allow_null=True)
    shell = serializers.CharField(required=False, allow_null=True)


class DownProductSerializer(serializers.ModelSerializer):
    """다운 상품 상세 직렬화"""
    brand_name = serializers.CharField(source='brand.name', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = DownProduct
        fields = [
            'id', 'brand_name', 'category_name', 'title', 'slug',
            'image_url', 'price', 'original_price', 'discount_rate',
            'seller', 'in_stock', 'score',
            'down_type', 'down_ratio', 'fill_power', 'hood', 'fit', 'shell',
            'created_at', 'updated_at'
        ]
