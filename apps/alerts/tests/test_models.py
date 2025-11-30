import pytest
from decimal import Decimal
from django.utils import timezone
from apps.alerts.models import Alert, EmailQueue


@pytest.mark.unit
class TestAlertModel:
    """Alert 모델 단위 테스트"""
    
    def test_create_alert(self, sample_alert):
        """알림 생성 테스트"""
        assert sample_alert.user_email == 'test@example.com'
        assert sample_alert.target_price == Decimal('150.00')
        assert sample_alert.is_active is True
    
    def test_alert_price_comparison(self, sample_alert):
        """알림 가격 비교 테스트"""
        # 목표 가격이 현재 가격보다 낮은지 확인
        assert sample_alert.target_price < sample_alert.current_price
    
    def test_deactivate_alert(self, sample_alert):
        """알림 비활성화 테스트"""
        sample_alert.is_active = False
        sample_alert.save()
        assert sample_alert.is_active is False
    
    def test_alert_str_representation(self, sample_alert):
        """알림 문자열 표현 테스트"""
        expected = f"Alert for {sample_alert.user_email} - {sample_alert.product_name}"
        assert str(sample_alert) == expected


@pytest.mark.unit
class TestEmailQueueModel:
    """EmailQueue 모델 단위 테스트"""
    
    def test_create_email_queue(self, db):
        """이메일 큐 생성 테스트"""
        email = EmailQueue.objects.create(
            recipient_email='test@example.com',
            subject='Test Alert',
            body='Your product is now available!',
            status='pending'
        )
        assert email.recipient_email == 'test@example.com'
        assert email.subject == 'Test Alert'
        assert email.status == 'pending'
        assert email.sent_at is None
    
    def test_email_queue_sent_status(self, db):
        """이메일 큐 발송 상태 테스트"""
        email = EmailQueue.objects.create(
            recipient_email='test@example.com',
            subject='Test',
            body='Body',
            status='pending'
        )
        
        # 발송 완료 처리
        email.status = 'sent'
        email.sent_at = timezone.now()
        email.save()
        
        assert email.status == 'sent'
        assert email.sent_at is not None
    
    def test_email_queue_failed_status(self, db):
        """이메일 큐 실패 상태 테스트"""
        email = EmailQueue.objects.create(
            recipient_email='invalid@',
            subject='Test',
            body='Body',
            status='failed',
            error_message='Invalid email address'
        )
        
        assert email.status == 'failed'
        assert email.error_message == 'Invalid email address'
