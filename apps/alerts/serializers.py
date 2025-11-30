"""
Alert serializers
"""
from rest_framework import serializers
from apps.alerts.models import Alert


class AlertSerializer(serializers.ModelSerializer):
    """알림 직렬화"""
    brand_slug = serializers.SlugField(write_only=True)
    category_slug = serializers.SlugField(write_only=True)
    
    brand = serializers.CharField(source='brand.name', read_only=True)
    category = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Alert
        fields = [
            'id', 'email',
            'brand', 'category', 'brand_slug', 'category_slug',
            'conditions', 'active', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']
    
    def create(self, validated_data):
        from apps.core.models import Brand, Category
        
        brand_slug = validated_data.pop('brand_slug')
        category_slug = validated_data.pop('category_slug')
        
        brand = Brand.objects.get(slug=brand_slug)
        category = Category.objects.get(slug=category_slug)
        
        alert = Alert.objects.create(
            brand=brand,
            category=category,
            **validated_data
        )
        
        return alert
