"""
Price History Model
상품 가격 추이 tracking
"""
from django.db import models
from apps.products.models import ProductBase


class PriceHistory(models.Model):
    """가격 이력 모델
    
    매일 자정에 Celery Beat가 모든 상품의 현재 가격을 스냅샷으로 저장
    가격 차트 API와 가격 하락 알림에 사용
    """
    # Generic Foreign Key로 모든 ProductBase 하위 모델 지원
    product_id = models.CharField(max_length=100, db_index=True, verbose_name='상품 ID')
    product_type = models.CharField(max_length=50, verbose_name='상품 타입')  # 'DownProduct', 'SlacksProduct' 등
    
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='가격')
    original_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='원가')
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='할인율')
    
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='기록 시간')
    
    class Meta:
        verbose_name = '가격 이력'
        verbose_name_plural = '가격 이력'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['product_id', '-recorded_at']),
            models.Index(fields=['recorded_at']),
        ]
        # 같은 날 같은 상품의 중복 기록 방지 (하루 1회만)
        constraints = [
            models.UniqueConstraint(
                fields=['product_id', 'recorded_at'],
                name='unique_product_price_per_day',
                violation_error_message='이미 오늘 가격이 기록되었습니다.'
            )
        ]
    
    def __str__(self):
        return f"{self.product_id} - {self.price}원 ({self.recorded_at.strftime('%Y-%m-%d')})"
    
    @property
    def price_change(self):
        """이전 기록 대비 가격 변동"""
        previous = PriceHistory.objects.filter(
            product_id=self.product_id,
            recorded_at__lt=self.recorded_at
        ).first()
        
        if previous:
            return self.price - previous.price
        return 0
    
    @property
    def discount_change(self):
        """이전 기록 대비 할인율 변동"""
        previous = PriceHistory.objects.filter(
            product_id=self.product_id,
            recorded_at__lt=self.recorded_at
        ).first()
        
        if previous:
            return self.discount_rate - previous.discount_rate
        return 0
    
    @classmethod
    def get_price_trend(cls, product_id: str, days: int = 30):
        """특정 상품의 가격 추이 조회
        
        Args:
            product_id: 상품 ID
            days: 조회 기간 (일)
        
        Returns:
            QuerySet of PriceHistory
        """
        from datetime.datetime import timedelta
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            product_id=product_id,
            recorded_at__gte=cutoff_date
        ).order_by('recorded_at')
    
    @classmethod
    def get_lowest_price(cls, product_id: str, days: int = 30):
        """특정 기간 내 최저가
        
        Args:
            product_id: 상품 ID
            days: 조회 기간 (일)
        
        Returns:
            PriceHistory instance or None
        """
        from datetime import timedelta
        from django.utils import timezone
        
        cutoff_date = timezone.now() - timedelta(days=days)
        return cls.objects.filter(
            product_id=product_id,
            recorded_at__gte=cutoff_date
        ).order_by('price').first()
    
    @classmethod
    def check_price_drop(cls, product_id: str, threshold_percent: float = 5.0):
        """최근 가격 하락 여부 확인
        
        Args:
            product_id: 상품 ID
            threshold_percent: 하락 임계값 (%)
        
        Returns:
            bool: threshold_percent 이상 하락했으면 True
        """
        records = cls.objects.filter(product_id=product_id).order_by('-recorded_at')[:2]
        
        if len(records) < 2:
            return False
        
        latest, previous = records[0], records[1]
        price_drop_percent = ((previous.price - latest.price) / previous.price) * 100
        
        return price_drop_percent >= threshold_percent
