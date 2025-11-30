"""
Celery configuration for E-wall project.
"""
import os
from celery import Celery
from celery.schedules import crontab

# Set the default Django settings module
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('ewall')

# Load configuration from Django settings
app.config_from_object('django.conf:settings', namespace='CELERY')

# Auto-discover tasks in all installed apps
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    'sync-naver-outlet-every-6-hours': {
        'task': 'apps.products.tasks.sync_naver_outlet_products',
        'schedule': crontab(minute=0, hour='*/6'),  # 6시간마다 (00:00, 06:00, 12:00, 18:00)
    },
    'snapshot-prices-daily': {
        'task': 'apps.products.tasks.snapshot_prices',
        'schedule': crontab(hour=1, minute=0),  # 매일 새벽 1시
    },
    'batch-generate-embeddings-daily': {
        'task': 'apps.products.tasks.batch_generate_embeddings',
        'schedule': crontab(hour=2, minute=30),  # 매일 새벽 2시 30분
        'args': (100,),  # 한 번에 100개씩 처리
    },
    'cleanup-old-price-history-weekly': {
        'task': 'apps.products.tasks.cleanup_old_price_history',
        'schedule': crontab(hour=3, minute=0, day_of_week=0),  # 매주 일요일 새벽 3시
        'args': (90,),  # 90일 이상 된 데이터 삭제
    },
    'cleanup-outdated-products-monthly': {
        'task': 'apps.products.tasks.cleanup_outdated_products',
        'schedule': crontab(hour=4, minute=0, day_of_month=1),  # 매월 1일 새벽 4시
        'args': (30,),  # 30일 이상 업데이트 안 된 상품 삭제
    },
    'check-price-changes-hourly': {
        'task': 'apps.alerts.tasks.check_price_changes',
        'schedule': crontab(minute=0),  # 매시간
    },
    'send-queued-emails-every-5-min': {
        'task': 'apps.alerts.tasks.send_queued_emails',
        'schedule': crontab(minute='*/5'),  # 5분마다
    },
    'aggregate-clicks-daily': {
        'task': 'apps.analytics.tasks.aggregate_daily_clicks',
        'schedule': crontab(hour=2, minute=0),  # 매일 오전 2시
    },
    'warmup-cache-morning': {
        'task': 'apps.core.tasks.warmup_cache',
        'schedule': crontab(hour=8, minute=0),  # 오전 8시
    },
    'warmup-cache-evening': {
        'task': 'apps.core.tasks.warmup_cache',
        'schedule': crontab(hour=18, minute=0),  # 오후 6시
    },
}

# Task routing
app.conf.task_routes = {
    'apps.products.tasks.*': {'queue': 'default'},
    'apps.products.tasks.generate_image_embedding': {'queue': 'embeddings'},  # 별도 큐로 처리
    'apps.alerts.tasks.send_queued_emails': {'queue': 'emails'},
    'apps.alerts.tasks.check_price_changes': {'queue': 'high_priority'},
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')
