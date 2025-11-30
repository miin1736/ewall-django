"""
Price History API Serializers
"""
from rest_framework import serializers
from apps.products.models import PriceHistory


class PriceHistorySerializer(serializers.ModelSerializer):
    """가격 이력 직렬화"""
    date = serializers.DateTimeField(source='recorded_at', format='%Y-%m-%d')
    
    class Meta:
        model = PriceHistory
        fields = ['date', 'price', 'original_price', 'discount_rate']


class PriceChartSerializer(serializers.Serializer):
    """가격 차트 데이터 직렬화
    
    Chart.js, Recharts 등과 호환되는 형식
    """
    product_id = serializers.CharField()
    product_title = serializers.CharField()
    period_days = serializers.IntegerField()
    
    # 차트 데이터
    labels = serializers.ListField(child=serializers.CharField())  # 날짜 레이블
    datasets = serializers.ListField(child=serializers.DictField())  # 차트 데이터셋
    
    # 통계
    stats = serializers.DictField()
    
    def to_representation(self, instance):
        """Chart.js 형식으로 직렬화"""
        return {
            'product_id': instance['product_id'],
            'product_title': instance['product_title'],
            'period_days': instance['period_days'],
            'chart': {
                'labels': instance['labels'],
                'datasets': instance['datasets']
            },
            'stats': instance['stats']
        }
