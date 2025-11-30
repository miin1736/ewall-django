"""
Alert and EmailQueue models
"""
import uuid
from django.db import models
from apps.core.models import Brand, Category


class Alert(models.Model):
    """가격 알림 모델"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(db_index=True, verbose_name='이메일')
    
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='브랜드')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='카테고리')
    
    # 조건 (유연한 JSON 구조)
    conditions = models.JSONField(default=dict, verbose_name='알림 조건')
    # 예시:
    # {
    #   "priceBelow": 100000,
    #   "discountAtLeast": 30,
    #   "downRatio": "90-10",
    #   "fillPowerMin": 750,
    #   "hood": false
    # }
    
    active = models.BooleanField(default=True, db_index=True, verbose_name='활성화')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '가격 알림'
        verbose_name_plural = '가격 알림'
        indexes = [
            models.Index(fields=['active', 'brand', 'category']),
            models.Index(fields=['email', 'active']),
        ]
    
    def __str__(self):
        return f"{self.email} - {self.brand.name} {self.category.name}"


class EmailQueue(models.Model):
    """이메일 발송 큐 모델"""
    REASON_CHOICES = [
        ('price_drop', '가격 하락'),
        ('restock', '재입고'),
        ('price_spike', '가격 급등'),
        ('trend_alert', '추세 알림'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    to_email = models.EmailField(verbose_name='수신자')
    subject = models.CharField(max_length=200, verbose_name='제목')
    body_html = models.TextField(verbose_name='내용 (HTML)')
    
    reason = models.CharField(
        max_length=50, 
        choices=REASON_CHOICES, 
        verbose_name='알림 사유'
    )
    
    product_id = models.CharField(max_length=100, verbose_name='상품 ID')
    product_data = models.JSONField(verbose_name='상품 스냅샷')
    
    sent = models.BooleanField(default=False, db_index=True, verbose_name='발송 완료')
    sent_at = models.DateTimeField(null=True, blank=True, verbose_name='발송 시각')
    error = models.TextField(null=True, blank=True, verbose_name='오류 메시지')
    
    # 연관 알림 (선택사항)
    alert = models.ForeignKey(
        'Alert',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='email_history',
        verbose_name='알림'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '이메일 큐'
        verbose_name_plural = '이메일 큐'
        indexes = [
            models.Index(fields=['sent', 'created_at']),
            models.Index(fields=['to_email']),
            models.Index(fields=['alert', 'created_at']),
        ]
    
    def __str__(self):
        status = "발송됨" if self.sent else "대기중"
        return f"{self.to_email} - {self.subject} ({status})"


class AlertHistory(models.Model):
    """알림 발송 이력 모델 (통계 및 분석용)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='history',
        verbose_name='알림'
    )
    
    product_id = models.CharField(max_length=100, db_index=True, verbose_name='상품 ID')
    product_data = models.JSONField(verbose_name='상품 스냅샷')
    
    # 매칭 정보
    matched_conditions = models.JSONField(verbose_name='매칭된 조건')
    priority = models.IntegerField(default=3, verbose_name='우선순위')
    
    # 발송 결과
    email_sent = models.BooleanField(default=False, verbose_name='이메일 발송 여부')
    email_sent_at = models.DateTimeField(null=True, blank=True, verbose_name='발송 시각')
    
    # 사용자 액션
    clicked = models.BooleanField(default=False, verbose_name='클릭 여부')
    clicked_at = models.DateTimeField(null=True, blank=True, verbose_name='클릭 시각')
    
    created_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='생성일')
    
    class Meta:
        verbose_name = '알림 이력'
        verbose_name_plural = '알림 이력'
        indexes = [
            models.Index(fields=['alert', 'created_at']),
            models.Index(fields=['product_id', 'created_at']),
            models.Index(fields=['email_sent', 'created_at']),
        ]
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.alert.email} - {self.product_id} ({self.created_at.strftime('%Y-%m-%d')})"


class AlertStatistics(models.Model):
    """알림 통계 모델 (일별 집계)"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    alert = models.ForeignKey(
        Alert,
        on_delete=models.CASCADE,
        related_name='statistics',
        verbose_name='알림'
    )
    
    date = models.DateField(db_index=True, verbose_name='날짜')
    
    # 매칭 통계
    total_matched = models.IntegerField(default=0, verbose_name='매칭 수')
    total_sent = models.IntegerField(default=0, verbose_name='발송 수')
    total_clicked = models.IntegerField(default=0, verbose_name='클릭 수')
    
    # 비율
    open_rate = models.FloatField(default=0.0, verbose_name='오픈율 (%)')
    click_rate = models.FloatField(default=0.0, verbose_name='클릭율 (%)')
    
    # 가격 통계
    avg_matched_price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='평균 매칭 가격'
    )
    avg_discount_rate = models.FloatField(
        null=True,
        blank=True,
        verbose_name='평균 할인율 (%)'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        verbose_name = '알림 통계'
        verbose_name_plural = '알림 통계'
        unique_together = [['alert', 'date']]
        indexes = [
            models.Index(fields=['alert', 'date']),
            models.Index(fields=['date']),
        ]
        ordering = ['-date']
    
    def __str__(self):
        return f"{self.alert.email} - {self.date} (매칭: {self.total_matched}, 발송: {self.total_sent})"
