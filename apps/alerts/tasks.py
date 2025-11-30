"""
Alert tasks
가격 변동 감지 및 이메일 발송
"""
from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task
def check_price_changes():
    """가격 변동 감지 및 알림 큐잉
    
    실행 주기: 1시간마다
    
    Steps:
        1. 최근 업데이트된 상품 조회
        2. 활성 알림 조건 조회
        3. 조건 매칭 (AlertMatcher)
        4. EmailQueue 추가
        5. 발송 트리거
    """
    from apps.alerts.models import Alert, EmailQueue
    from apps.alerts.services.matcher import AlertMatcher
    from apps.products.models import (
        DownProduct, SlacksProduct, JeansProduct,
        CrewneckProduct, LongSleeveProduct, CoatProduct
    )
    
    # 최근 1시간 내 업데이트된 상품
    threshold = timezone.now() - timezone.timedelta(hours=1)
    
    # 모든 상품 모델에서 조회
    product_models = [
        DownProduct, SlacksProduct, JeansProduct,
        CrewneckProduct, LongSleeveProduct, CoatProduct
    ]
    
    queued = 0
    matcher = AlertMatcher()
    
    for model in product_models:
        recent_products = model.objects.filter(
            updated_at__gte=threshold,
            in_stock=True
        ).select_related('brand', 'category')
        
        # 활성 알림 조회
        alerts = Alert.objects.filter(active=True).select_related('brand', 'category')
        
        for product in recent_products:
            for alert in alerts:
                # 브랜드/카테고리 매칭
                if alert.brand_id != product.brand_id or alert.category_id != product.category_id:
                    continue
                
                # 조건 매칭
                if not matcher.matches(product, alert.conditions):
                    continue
                
                # 이메일 큐 추가
                try:
                    html_body = render_to_string('emails/price_drop.html', {
                        'product': product,
                        'alert': alert,
                    })
                    
                    EmailQueue.objects.create(
                        to_email=alert.email,
                        subject=f"가격 하락: {product.title[:50]}...",
                        body_html=html_body,
                        reason='price_drop',
                        product_id=product.id,
                        product_data={
                            'title': product.title,
                            'price': float(product.price),
                            'discount_rate': float(product.discount_rate),
                            'image_url': product.image_url,
                        }
                    )
                    queued += 1
                    
                except Exception as e:
                    logger.error(f"Failed to queue email: {e}")
                    continue
    
    logger.info(f"Queued {queued} alert emails")
    
    # 발송 트리거
    if queued > 0:
        send_queued_emails.delay()
    
    return {'queued': queued}


@shared_task(bind=True, max_retries=3)
def send_queued_emails(self, batch_size: int = 100):
    """이메일 큐 발송
    
    실행 주기: 5분마다
    """
    from apps.alerts.models import EmailQueue
    
    pending = EmailQueue.objects.filter(sent=False).order_by('created_at')[:batch_size]
    
    sent_count = 0
    error_count = 0
    
    for email in pending:
        try:
            send_mail(
                subject=email.subject,
                message='',
                html_message=email.body_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email.to_email],
                fail_silently=False,
            )
            
            email.sent = True
            email.sent_at = timezone.now()
            email.save()
            
            sent_count += 1
            logger.info(f"Sent email to {email.to_email}")
            
        except Exception as e:
            email.error = str(e)
            email.save()
            error_count += 1
            logger.error(f"Email send failed for {email.to_email}: {e}")
    
    logger.info(f"Email batch complete: sent={sent_count}, errors={error_count}")
    
    return {'sent': sent_count, 'errors': error_count}


@shared_task
def check_price_drops():
    """PriceHistory 기반 가격 하락 감지 및 알림
    
    실행: snapshot_prices 완료 후 트리거
    
    Steps:
        1. 오늘 기록된 PriceHistory 조회
        2. 전일 대비 가격 하락한 상품 필터링
        3. 해당 상품을 구독 중인 Alert 조회
        4. 조건 매칭 후 EmailQueue 추가
    """
    from apps.alerts.models import Alert, EmailQueue
    from apps.products.models import PriceHistory
    from django.utils import timezone
    from datetime import timedelta
    
    logger.info("Checking for price drops")
    
    # 오늘 기록
    today = timezone.now().date()
    today_records = PriceHistory.objects.filter(recorded_at__date=today)
    
    # 어제 날짜
    yesterday = today - timedelta(days=1)
    
    queued = 0
    checked = 0
    
    for today_record in today_records:
        checked += 1
        
        # 어제 기록 조회
        try:
            yesterday_record = PriceHistory.objects.get(
                product_id=today_record.product_id,
                recorded_at__date=yesterday
            )
        except PriceHistory.DoesNotExist:
            continue
        
        # 가격 하락 확인
        price_drop = yesterday_record.price - today_record.price
        if price_drop <= 0:
            continue  # 가격이 오르거나 동일
        
        price_drop_percent = (price_drop / yesterday_record.price) * 100
        
        # 해당 상품을 구독 중인 Alert 조회
        alerts = Alert.objects.filter(
            active=True,
            # 조건에 price_drop_threshold가 있는 경우만
            conditions__has_key='price_drop_threshold'
        )
        
        for alert in alerts:
            threshold = alert.conditions.get('price_drop_threshold', 5.0)
            
            if price_drop_percent >= threshold:
                # 이메일 큐 추가
                try:
                    # 실제 Product 객체 조회 (이메일 템플릿용)
                    from apps.products.models import (
                        DownProduct, SlacksProduct, JeansProduct,
                        CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
                    )
                    
                    # product_type으로 모델 선택
                    model_map = {
                        'DownProduct': DownProduct,
                        'SlacksProduct': SlacksProduct,
                        'JeansProduct': JeansProduct,
                        'CrewneckProduct': CrewneckProduct,
                        'LongSleeveProduct': LongSleeveProduct,
                        'CoatProduct': CoatProduct,
                        'GenericProduct': GenericProduct,
                    }
                    
                    model = model_map.get(today_record.product_type)
                    if not model:
                        continue
                    
                    product = model.objects.get(id=today_record.product_id)
                    
                    html_body = render_to_string('emails/price_drop_alert.html', {
                        'product': product,
                        'alert': alert,
                        'price_drop': float(price_drop),
                        'price_drop_percent': float(price_drop_percent),
                        'previous_price': float(yesterday_record.price),
                        'current_price': float(today_record.price),
                    })
                    
                    EmailQueue.objects.create(
                        to_email=alert.email,
                        subject=f"💰 가격 {price_drop_percent:.1f}% 하락: {product.title[:40]}",
                        body_html=html_body,
                        reason='price_drop_alert',
                        product_id=product.id,
                        product_data={
                            'title': product.title,
                            'price': float(today_record.price),
                            'previous_price': float(yesterday_record.price),
                            'price_drop': float(price_drop),
                            'price_drop_percent': float(price_drop_percent),
                            'image_url': product.image_url,
                        }
                    )
                    queued += 1
                    
                except Exception as e:
                    logger.error(f"Failed to queue price drop email for {today_record.product_id}: {e}")
                    continue
    
    logger.info(f"Price drop check complete: checked={checked}, queued={queued}")
    
    # 발송 트리거
    if queued > 0:
        send_queued_emails.delay()
    
    return {'checked': checked, 'queued': queued}
