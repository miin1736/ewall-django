"""
Analytics tasks
클릭 데이터 집계
"""
from celery import shared_task
from django.utils import timezone
from django.db.models import Count
import logging

logger = logging.getLogger(__name__)


@shared_task
def aggregate_daily_clicks():
    """일일 클릭 데이터 집계
    
    실행 주기: 매일 오전 2시
    
    Steps:
        1. 전날 클릭 데이터 조회
        2. 브랜드×카테고리별 집계
        3. DailyClickAggregate 생성
    """
    from apps.analytics.models import Click, DailyClickAggregate
    
    # 전날 날짜
    yesterday = (timezone.now() - timezone.timedelta(days=1)).date()
    
    # 전날 클릭 데이터
    clicks = Click.objects.filter(
        timestamp__date=yesterday
    ).values('brand', 'category').annotate(
        click_count=Count('id'),
        unique_products=Count('product_id', distinct=True)
    )
    
    aggregated = 0
    
    for click_data in clicks:
        DailyClickAggregate.objects.update_or_create(
            date=yesterday,
            brand=click_data['brand'],
            category=click_data['category'],
            defaults={
                'click_count': click_data['click_count'],
                'unique_products': click_data['unique_products'],
            }
        )
        aggregated += 1
    
    logger.info(f"Aggregated {aggregated} daily click records for {yesterday}")
    
    return {
        'date': str(yesterday),
        'aggregated': aggregated
    }
