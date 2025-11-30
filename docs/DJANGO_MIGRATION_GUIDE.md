# E-wall Django Migration Guide

> **목적**: 이 문서를 새로운 프로젝트에 업로드하면 AI 에이전트가 Next.js → Django DRF로 자동 마이그레이션할 수 있도록 모든 정보를 포함합니다.

---

## 📋 프로젝트 개요

### 서비스명
**E-wall (이월)** - 아웃도어 이월 상품 검색 플랫폼

### 비즈니스 모델
- 제휴 마케팅 플랫폼 (쿠팡 파트너스, 링크프라이스 등)
- 커미션 기반 수익 모델 (3-5%)
- B2C SaaS 서비스

### 핵심 가치 제안
1. **전문 속성 필터**: 다운 비율, 필파워, 핏, 소재 등 상세 검색
2. **다중 판매처 가격 비교**: 여러 제휴사 가격 실시간 비교
3. **가격 알림**: 조건 충족 시 자동 이메일 알림
4. **SEO 최적화**: 브랜드×카테고리 조합별 랜딩 페이지 자동 생성

---

## 🎯 주요 기능 (GitHub Issues 기반)

### Issue #1: 데이터 파이프라인 구축 및 속성 정규화
**목표**: 제휴사 피드 수집 → 속성 정규화 → DB 저장

**구현 내용**:
```typescript
// 현재: scripts/parseFeeds.ts
- 제휴사 API 호출 (fetchFeed)
- 속성 추출 (lib/attributes/extractAttributes)
  - 정규식 기반: 다운비율 (90/10), 필파워 (800FP), 후드, 핏 등
- 정규화 (normalize)
- JSONL 스냅샷 저장 (out/products.normalized.json)
```

**Django 요구사항**:
- Celery 주기 태스크 (6시간마다)
- Pydantic 기반 속성 검증
- PostgreSQL bulk upsert
- 실패 로그 (structured logging)

---

### Issue #3: 랜딩 및 고급 필터 UI
**목표**: 브랜드×카테고리 페이지 + 속성 필터링

**현재 구현**:
```typescript
// app/(ewall)/[brand]/[category]/page.tsx
- SSR/SSG 지원
- URL: /BrandA/down?downRatio=90-10&fillPowerMin=750&sort=discount
- 필터: downType, downRatio, fillPower, hood, fit, shell
- 정렬: discount, priceAsc, priceDesc, new
- JSON-LD 구조화 데이터
- 동적 sitemap 생성
```

**Django 요구사항**:
- Django 템플릿 SSR
- DRF API 엔드포인트 (`/api/products/{brand}/{category}/`)
- django-filter 백엔드
- Redis 캐싱 (5분)
- SEO Meta 태그 자동 생성

---

### Issue #4: 알림 및 리텐션 기능
**목표**: 가격 변동 감지 + 이메일 알림

**현재 구현**:
```typescript
// scripts/cron/syncOffers.ts
- 이전 스냅샷과 diff 계산
- 가격 하락/재입고 감지
- 조건 매칭 (matchesAlert)
- 이메일 큐 추가 (emails.queue.jsonl)
```

**Django 요구사항**:
- Alert 모델 (JSONField conditions)
- Celery 변동 감지 태스크 (1시간마다)
- EmailQueue 모델
- SMTP 비동기 발송
- 클릭 트래킹 (/api/out)

---

### Issue #5: CI/CD 스모크 테스트
**목표**: 품질 보증 자동화

**현재 구현**:
```yaml
# .github/workflows/ewall-smoke.yml
- Node 18/20 매트릭스
- 빌드 성공
- 라우트 200 응답
- JSON-LD 검증
- 피드 파서 실행
- 필터 스모크 테스트
```

**Django 요구사항**:
- pytest + pytest-django
- coverage 80% 이상
- 스모크 테스트 (API, 템플릿, Celery)
- GitHub Actions CI/CD

---

## 📐 데이터 모델 설계

### 1. Product (다형성 - Multi-Table Inheritance)

**ProductBase (Abstract)**:
```python
class ProductBase(models.Model):
    id = CharField(max_length=100, primary_key=True)
    brand = ForeignKey(Brand)
    category = ForeignKey(Category)
    
    title = CharField(max_length=500)
    slug = SlugField(unique=True)
    image_url = URLField()
    
    price = DecimalField(max_digits=10, decimal_places=0)
    original_price = DecimalField(max_digits=10, decimal_places=0)
    discount_rate = DecimalField(max_digits=5, decimal_places=2)
    currency = CharField(max_length=3, default='KRW')
    
    seller = CharField(max_length=100)
    deeplink = URLField(max_length=2000)
    in_stock = BooleanField(default=True)
    
    score = FloatField(default=0.0)  # 신뢰도 점수
    source = CharField(max_length=50)  # 제휴사명
    
    created_at = DateTimeField(auto_now_add=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        abstract = True
        indexes = [
            Index(fields=['brand', 'category', '-discount_rate']),
            Index(fields=['in_stock', '-updated_at']),
        ]
```

**카테고리별 모델 (7개)**:
```python
class DownProduct(ProductBase):
    down_type = CharField(max_length=50, null=True)  # goose, duck, synthetic
    down_ratio = CharField(max_length=20, null=True)  # 90-10, 80-20, 70-30
    fill_power = IntegerField(null=True)  # 300-1000
    hood = BooleanField(null=True)
    fit = CharField(max_length=50, null=True)  # slim, regular, relaxed, oversized
    shell = CharField(max_length=50, null=True)  # nylon, polyester, gore-tex

class SlacksProduct(ProductBase):
    waist_type = CharField(max_length=50, null=True)  # high, mid, low
    leg_opening = CharField(max_length=50, null=True)  # tapered, straight, wide
    stretch = BooleanField(null=True)
    pleats = CharField(max_length=50, null=True)  # single, double, none
    fit = CharField(max_length=50, null=True)
    shell = CharField(max_length=50, null=True)

class JeansProduct(ProductBase):
    wash = CharField(max_length=50, null=True)  # light, medium, dark, black
    cut = CharField(max_length=50, null=True)  # skinny, slim, straight, bootcut, wide
    rise = CharField(max_length=50, null=True)  # low, mid, high
    stretch = BooleanField(null=True)
    distressed = BooleanField(null=True)

class CrewneckProduct(ProductBase):
    neckline = CharField(max_length=50, null=True)  # crew, mock, v-neck, henley
    sleeve_length = CharField(max_length=50, null=True)  # short, long
    pattern = CharField(max_length=50, null=True)  # solid, stripe, graphic
    fit = CharField(max_length=50, null=True)
    shell = CharField(max_length=50, null=True)

class LongSleeveProduct(ProductBase):
    neckline = CharField(max_length=50, null=True)
    sleeve_type = CharField(max_length=50, null=True)  # raglan, set-in
    layering = BooleanField(null=True)  # 레이어링 가능 여부
    fit = CharField(max_length=50, null=True)
    shell = CharField(max_length=50, null=True)

class CoatProduct(ProductBase):
    length = CharField(max_length=50, null=True)  # short, mid, long
    closure = CharField(max_length=50, null=True)  # button, zip, belt
    lining = CharField(max_length=50, null=True)  # full, half, none
    hood = BooleanField(null=True)
    fit = CharField(max_length=50, null=True)
    shell = CharField(max_length=50, null=True)

class GenericProduct(ProductBase):
    # 기타 모든 카테고리
    fit = CharField(max_length=50, null=True)
    shell = CharField(max_length=50, null=True)
```

**인덱스 전략**:
```python
# 복합 인덱스 (빠른 필터링)
Index(fields=['down_ratio', 'fill_power'])  # DownProduct
Index(fields=['waist_type', 'leg_opening'])  # SlacksProduct
Index(fields=['wash', 'cut'])  # JeansProduct
```

---

### 2. Alert (알림 조건)

```python
class Alert(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    email = EmailField(db_index=True)
    
    brand = ForeignKey(Brand, on_delete=CASCADE)
    category = ForeignKey(Category, on_delete=CASCADE)
    
    # 조건 (유연한 JSON 구조)
    conditions = JSONField(default=dict)
    # 예시:
    # {
    #   "priceBelow": 100000,
    #   "discountAtLeast": 30,
    #   "downRatio": "90-10",
    #   "fillPowerMin": 750,
    #   "hood": false
    # }
    
    active = BooleanField(default=True, db_index=True)
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['active', 'brand', 'category']),
        ]
```

---

### 3. EmailQueue (발송 큐)

```python
class EmailQueue(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    
    to_email = EmailField()
    subject = CharField(max_length=200)
    body_html = TextField()
    
    reason = CharField(max_length=50, choices=[
        ('price_drop', 'Price Drop'),
        ('restock', 'Restock'),
    ])
    
    product_id = CharField(max_length=100)
    product_data = JSONField()  # 스냅샷 (제목, 가격 등)
    
    sent = BooleanField(default=False, db_index=True)
    sent_at = DateTimeField(null=True)
    error = TextField(null=True)
    
    created_at = DateTimeField(auto_now_add=True)
    
    class Meta:
        indexes = [
            Index(fields=['sent', 'created_at']),
        ]
```

---

### 4. Click (클릭 추적)

```python
class Click(models.Model):
    id = UUIDField(primary_key=True, default=uuid.uuid4)
    
    product_id = CharField(max_length=100, db_index=True)
    brand = CharField(max_length=100)
    category = CharField(max_length=50)
    
    referrer = CharField(max_length=200, null=True)  # 유입 경로
    user_agent = CharField(max_length=500, null=True)
    
    timestamp = DateTimeField(auto_now_add=True, db_index=True)
    
    class Meta:
        indexes = [
            Index(fields=['timestamp']),
            Index(fields=['product_id', 'timestamp']),
        ]
```

---

## 🔧 속성 정규화 로직

### 정규식 패턴 (lib/attributes/index.ts → Python)

```python
import re
from typing import Optional, Dict, Any

class AttributeExtractor:
    """텍스트에서 상품 속성 추출"""
    
    PATTERNS = {
        'down_type': {
            'goose': re.compile(r'거위|goose|구스', re.IGNORECASE),
            'duck': re.compile(r'오리|duck|덕', re.IGNORECASE),
            'synthetic': re.compile(r'합성|synthetic|프리마로프트', re.IGNORECASE),
        },
        'down_ratio': {
            '90-10': re.compile(r'90[/-]10|90/10|90-10'),
            '80-20': re.compile(r'80[/-]20|80/20|80-20'),
            '70-30': re.compile(r'70[/-]30|70/30|70-30'),
            '60-40': re.compile(r'60[/-]40|60/40|60-40'),
        },
        'fill_power': re.compile(r'(\d{3,4})\s*(?:fp|fill|필파워|필)', re.IGNORECASE),
        'hood': {
            True: re.compile(r'후드|hood|hooded', re.IGNORECASE),
            False: re.compile(r'노후드|no hood|hoodless', re.IGNORECASE),
        },
        'fit': {
            'slim': re.compile(r'슬림|slim|fitted', re.IGNORECASE),
            'regular': re.compile(r'레귤러|regular|classic|standard', re.IGNORECASE),
            'relaxed': re.compile(r'릴렉스|relaxed|loose', re.IGNORECASE),
            'oversized': re.compile(r'오버사이즈|oversized|큰|빅', re.IGNORECASE),
        },
        'shell': {
            'nylon': re.compile(r'나일론|nylon', re.IGNORECASE),
            'polyester': re.compile(r'폴리에스터|polyester', re.IGNORECASE),
            'gore-tex': re.compile(r'고어텍스|gore-?tex', re.IGNORECASE),
            'cotton': re.compile(r'코튼|cotton|면', re.IGNORECASE),
            'wool': re.compile(r'울|wool|양모', re.IGNORECASE),
        },
        'waist_type': {
            'high': re.compile(r'하이웨이스트|high waist|high-rise', re.IGNORECASE),
            'mid': re.compile(r'미드웨이스트|mid waist|mid-rise|regular', re.IGNORECASE),
            'low': re.compile(r'로우웨이스트|low waist|low-rise', re.IGNORECASE),
        },
        'leg_opening': {
            'tapered': re.compile(r'테이퍼드|tapered|슬림|slim', re.IGNORECASE),
            'straight': re.compile(r'스트레이트|straight', re.IGNORECASE),
            'wide': re.compile(r'와이드|wide|넓은', re.IGNORECASE),
        },
        'wash': {
            'light': re.compile(r'라이트|light|밝은|연한', re.IGNORECASE),
            'medium': re.compile(r'미디엄|medium|중간', re.IGNORECASE),
            'dark': re.compile(r'다크|dark|어두운|진한', re.IGNORECASE),
            'black': re.compile(r'블랙|black|검정', re.IGNORECASE),
        },
        'cut': {
            'skinny': re.compile(r'스키니|skinny', re.IGNORECASE),
            'slim': re.compile(r'슬림|slim', re.IGNORECASE),
            'straight': re.compile(r'스트레이트|straight', re.IGNORECASE),
            'bootcut': re.compile(r'부츠컷|bootcut|boot cut', re.IGNORECASE),
            'wide': re.compile(r'와이드|wide', re.IGNORECASE),
        },
    }
    
    @classmethod
    def extract(cls, text: str, category: str) -> Dict[str, Any]:
        """텍스트에서 속성 추출
        
        Args:
            text: 상품 제목 + 설명
            category: 카테고리 slug (down, slacks, jeans 등)
        
        Returns:
            추출된 속성 딕셔너리
        """
        attrs = {}
        
        # 카테고리별 속성 추출
        if category == 'down':
            # Down Type
            for dtype, pattern in cls.PATTERNS['down_type'].items():
                if pattern.search(text):
                    attrs['down_type'] = dtype
                    break
            
            # Down Ratio
            for ratio, pattern in cls.PATTERNS['down_ratio'].items():
                if pattern.search(text):
                    attrs['down_ratio'] = ratio
                    break
            
            # Fill Power (숫자 추출)
            fp_match = cls.PATTERNS['fill_power'].search(text)
            if fp_match:
                attrs['fill_power'] = int(fp_match.group(1))
            
            # Hood
            for hood_val, pattern in cls.PATTERNS['hood'].items():
                if pattern.search(text):
                    attrs['hood'] = hood_val
                    break
            
            # Fit
            for fit_val, pattern in cls.PATTERNS['fit'].items():
                if pattern.search(text):
                    attrs['fit'] = fit_val
                    break
            
            # Shell
            for shell_val, pattern in cls.PATTERNS['shell'].items():
                if pattern.search(text):
                    attrs['shell'] = shell_val
                    break
        
        elif category == 'slacks':
            # Waist Type
            for wtype, pattern in cls.PATTERNS['waist_type'].items():
                if pattern.search(text):
                    attrs['waist_type'] = wtype
                    break
            
            # Leg Opening
            for ltype, pattern in cls.PATTERNS['leg_opening'].items():
                if pattern.search(text):
                    attrs['leg_opening'] = ltype
                    break
            
            # Stretch (boolean)
            if re.search(r'스트레치|stretch|신축', text, re.IGNORECASE):
                attrs['stretch'] = True
            
            # Pleats
            if re.search(r'더블.*플리츠|double.*pleat', text, re.IGNORECASE):
                attrs['pleats'] = 'double'
            elif re.search(r'싱글.*플리츠|single.*pleat', text, re.IGNORECASE):
                attrs['pleats'] = 'single'
            elif re.search(r'노플리츠|no.*pleat', text, re.IGNORECASE):
                attrs['pleats'] = 'none'
        
        elif category == 'jeans':
            # Wash
            for wash_val, pattern in cls.PATTERNS['wash'].items():
                if pattern.search(text):
                    attrs['wash'] = wash_val
                    break
            
            # Cut
            for cut_val, pattern in cls.PATTERNS['cut'].items():
                if pattern.search(text):
                    attrs['cut'] = cut_val
                    break
            
            # Rise
            for rise_val, pattern in cls.PATTERNS['waist_type'].items():
                if pattern.search(text):
                    attrs['rise'] = rise_val
                    break
            
            # Stretch
            if re.search(r'스트레치|stretch|신축', text, re.IGNORECASE):
                attrs['stretch'] = True
            
            # Distressed
            if re.search(r'디스트레스|distressed|워싱|빈티지', text, re.IGNORECASE):
                attrs['distressed'] = True
        
        # 기타 카테고리 (crewneck, long-sleeve, coat) 로직 추가...
        
        return attrs
```

---

## 🔄 Celery 태스크 정의

### 1. 피드 동기화 (sync_feeds)

```python
# apps/products/tasks.py
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)

@shared_task(bind=True, max_retries=3)
def sync_feeds(self, source: str = 'coupang'):
    """제휴사 피드 동기화
    
    실행 주기: 6시간마다 (Celery Beat)
    
    Steps:
        1. 제휴사 API 호출 (FeedFetcher)
        2. 데이터 정규화 (ProductNormalizer)
        3. 속성 추출 (AttributeExtractor)
        4. DB bulk upsert
        5. 변동 감지 트리거
    """
    try:
        from apps.products.services.fetcher import FeedFetcher
        from apps.products.services.normalizer import ProductNormalizer
        from apps.products.models.categories import DownProduct, SlacksProduct
        
        # 1. 피드 가져오기
        fetcher = FeedFetcher(source=source)
        raw_items = fetcher.fetch()
        logger.info(f"Fetched {len(raw_items)} items from {source}")
        
        # 2. 정규화
        normalizer = ProductNormalizer()
        products = [normalizer.normalize(item) for item in raw_items]
        logger.info(f"Normalized {len(products)} products")
        
        # 3. DB upsert (트랜잭션)
        created, updated = 0, 0
        
        with transaction.atomic():
            for product_data in products:
                category = product_data.pop('category')
                
                model_map = {
                    'down': DownProduct,
                    'slacks': SlacksProduct,
                    'jeans': JeansProduct,
                    'crewneck': CrewneckProduct,
                    'long-sleeve': LongSleeveProduct,
                    'coat': CoatProduct,
                }
                
                model = model_map.get(category.slug)
                if not model:
                    logger.warning(f"Unknown category: {category.slug}")
                    continue
                
                product, is_created = model.objects.update_or_create(
                    id=product_data['id'],
                    defaults={**product_data, 'updated_at': timezone.now()}
                )
                
                if is_created:
                    created += 1
                else:
                    updated += 1
        
        logger.info(f"Sync complete: created={created}, updated={updated}")
        
        # 4. 가격 변동 감지 트리거
        from apps.alerts.tasks import check_price_changes
        check_price_changes.delay()
        
        return {'created': created, 'updated': updated}
        
    except Exception as exc:
        logger.error(f"Feed sync failed: {exc}")
        raise self.retry(exc=exc, countdown=300)  # 5분 후 재시도
```

---

### 2. 가격 변동 감지 (check_price_changes)

```python
# apps/alerts/tasks.py
from celery import shared_task
from django.utils import timezone
from django.template.loader import render_to_string

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
    from apps.products.models.categories import DownProduct
    
    # 최근 1시간 내 업데이트
    threshold = timezone.now() - timezone.timedelta(hours=1)
    recent_products = DownProduct.objects.filter(
        updated_at__gte=threshold
    ).select_related('brand', 'category')
    
    alerts = Alert.objects.filter(active=True).select_related('brand', 'category')
    
    matcher = AlertMatcher()
    queued = 0
    
    for product in recent_products:
        for alert in alerts:
            # 브랜드/카테고리 매칭
            if alert.brand_id != product.brand_id or alert.category_id != product.category_id:
                continue
            
            # 조건 매칭
            if not matcher.matches(product, alert.conditions):
                continue
            
            # 이메일 큐 추가
            EmailQueue.objects.create(
                to_email=alert.email,
                subject=f"가격 하락: {product.title}",
                body_html=render_to_string('emails/price_drop.html', {
                    'product': product,
                    'alert': alert,
                }),
                reason='price_drop',
                product_id=product.id,
                product_data={
                    'title': product.title,
                    'price': float(product.price),
                    'discount_rate': float(product.discount_rate),
                }
            )
            queued += 1
    
    logger.info(f"Queued {queued} alert emails")
    
    # 발송 트리거
    send_queued_emails.delay()


@shared_task(bind=True, max_retries=3)
def send_queued_emails(self, batch_size=100):
    """이메일 큐 발송
    
    실행 주기: 5분마다
    """
    from django.core.mail import send_mail
    from apps.alerts.models import EmailQueue
    
    pending = EmailQueue.objects.filter(sent=False)[:batch_size]
    
    for email in pending:
        try:
            send_mail(
                subject=email.subject,
                message='',
                html_message=email.body_html,
                from_email='noreply@ewall.com',
                recipient_list=[email.to_email],
                fail_silently=False,
            )
            
            email.sent = True
            email.sent_at = timezone.now()
            email.save()
            
        except Exception as e:
            email.error = str(e)
            email.save()
            logger.error(f"Email send failed: {e}")
```

---

### 3. Celery Beat 스케줄

```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('ewall')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.beat_schedule = {
    'sync-feeds-every-6-hours': {
        'task': 'apps.products.tasks.sync_feeds',
        'schedule': crontab(minute=0, hour='*/6'),
        'args': ('coupang',)
    },
    'check-price-changes-hourly': {
        'task': 'apps.alerts.tasks.check_price_changes',
        'schedule': crontab(minute=0),
    },
    'send-queued-emails-every-5-min': {
        'task': 'apps.alerts.tasks.send_queued_emails',
        'schedule': crontab(minute='*/5'),
    },
}
```

---

## 🌐 API 엔드포인트 설계

### 1. 상품 목록 API

**Endpoint**: `GET /api/products/{brand_slug}/{category_slug}/`

**Query Parameters**:
```
?downRatio=90-10          # 다운비율 필터
&fillPowerMin=750         # 필파워 최소값
&priceMax=100000          # 최대 가격
&discountMin=30           # 최소 할인율
&hood=true                # 후드 유무
&fit=slim                 # 핏
&sort=discount            # 정렬 (discount, price-low, price-high, newest)
&page=1                   # 페이지
&page_size=20             # 페이지 크기
```

**Response**:
```json
{
  "products": [
    {
      "id": "coupang-ex-001",
      "brand_name": "BrandA",
      "category_name": "Down",
      "title": "BrandA 다운 재킷 800FP 90/10",
      "slug": "branda-down-jacket-800fp-90-10",
      "image_url": "https://...",
      "price": "89000",
      "original_price": "129000",
      "discount_rate": "31.00",
      "in_stock": true,
      "score": 85.0,
      "down_type": "goose",
      "down_ratio": "90-10",
      "fill_power": 800,
      "hood": false,
      "fit": "regular",
      "shell": "nylon"
    }
  ],
  "total": 15,
  "page": 1,
  "page_size": 20,
  "total_pages": 1
}
```

**구현**:
```python
# apps/products/views/list.py
from rest_framework.views import APIView
from rest_framework.response import Response
from django.core.cache import cache

class ProductListAPIView(APIView):
    def get(self, request, brand_slug, category_slug):
        # 캐시 확인 (5분)
        cache_key = f"products:{brand_slug}:{category_slug}:{request.GET.urlencode()}"
        cached = cache.get(cache_key)
        if cached:
            return Response(cached)
        
        # 모델 선택
        model_map = {
            'down': DownProduct,
            'slacks': SlacksProduct,
            # ...
        }
        model = model_map[category_slug]
        
        # 필터링
        queryset = model.objects.filter(
            brand__slug=brand_slug,
            in_stock=True
        ).select_related('brand', 'category')
        
        # django-filter 적용
        filterset = ProductFilterSet(request.GET, queryset=queryset)
        queryset = filterset.qs
        
        # 정렬
        sort = request.GET.get('sort', 'discount')
        sort_map = {
            'discount': '-discount_rate',
            'price-low': 'price',
            'price-high': '-price',
            'newest': '-created_at',
        }
        queryset = queryset.order_by(sort_map[sort])
        
        # 페이지네이션
        page = int(request.GET.get('page', 1))
        page_size = int(request.GET.get('page_size', 20))
        start = (page - 1) * page_size
        
        products = queryset[start:start + page_size]
        total = queryset.count()
        
        # 직렬화
        serializer = ProductListSerializer(products, many=True)
        
        response_data = {
            'products': serializer.data,
            'total': total,
            'page': page,
            'page_size': page_size,
            'total_pages': (total + page_size - 1) // page_size
        }
        
        # 캐시 저장
        cache.set(cache_key, response_data, timeout=300)
        
        return Response(response_data)
```

---

### 2. 알림 생성 API

**Endpoint**: `POST /api/alerts/`

**Request Body**:
```json
{
  "email": "user@example.com",
  "brand_slug": "branda",
  "category_slug": "down",
  "conditions": {
    "priceBelow": 100000,
    "discountAtLeast": 30,
    "downRatio": "90-10",
    "fillPowerMin": 750,
    "hood": false
  }
}
```

**Response**:
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "brand": "BrandA",
  "category": "Down",
  "conditions": {...},
  "active": true,
  "created_at": "2025-11-21T10:00:00Z"
}
```

---

### 3. 클릭 트래킹 API

**Endpoint**: `GET /api/out/?productId={id}&subId={tracking_id}`

**동작**:
1. Click 레코드 생성
2. 302 리다이렉트 → 제휴 딥링크

**구현**:
```python
# apps/analytics/views.py
from django.http import HttpResponseRedirect
from apps.analytics.models import Click
from apps.products.models.categories import DownProduct

class OutboundRedirectView(APIView):
    def get(self, request):
        product_id = request.GET.get('productId')
        sub_id = request.GET.get('subId', '')
        
        # 상품 조회
        product = DownProduct.objects.get(id=product_id)
        
        # 클릭 기록
        Click.objects.create(
            product_id=product_id,
            brand=product.brand.name,
            category=product.category.name,
            referrer=request.META.get('HTTP_REFERER'),
            user_agent=request.META.get('HTTP_USER_AGENT'),
        )
        
        # 딥링크에 subId 추가
        deeplink = f"{product.deeplink}&subId={sub_id}"
        
        return HttpResponseRedirect(deeplink)
```

---

## 📄 Django 템플릿 (SSR)

### 랜딩 페이지

**URL**: `/{brand_slug}/{category_slug}/`

**템플릿**: `templates/frontend/landing.html`

```django
{% extends 'base.html' %}
{% load static %}

{% block title %}{{ brand.name }} {{ category.name }} 이월 특가 - E-wall{% endblock %}

{% block meta %}
<meta name="description" content="{{ brand.name }} {{ category.name }} 최대 할인 모음">
<meta property="og:title" content="{{ brand.name }} {{ category.name }} 이월 특가">

{# JSON-LD #}
<script type="application/ld+json">
{{ json_ld|safe }}
</script>
{% endblock %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <h1 class="text-3xl font-bold mb-6">
        {{ brand.name }} {{ category.name }} 이월 특가
    </h1>
    
    {# 필터 컴포넌트 #}
    <div class="filters mb-6">
        <form method="get" id="filter-form">
            {% if category.slug == 'down' %}
                <select name="downRatio">
                    <option value="">다운비율</option>
                    <option value="90-10">90/10</option>
                    <option value="80-20">80/20</option>
                    <option value="70-30">70/30</option>
                </select>
                
                <input type="number" name="fillPowerMin" placeholder="최소 필파워">
                
                <select name="hood">
                    <option value="">후드</option>
                    <option value="true">있음</option>
                    <option value="false">없음</option>
                </select>
            {% endif %}
            
            <select name="sort">
                <option value="discount">할인율 순</option>
                <option value="price-low">가격 낮은 순</option>
                <option value="price-high">가격 높은 순</option>
                <option value="newest">최신 순</option>
            </select>
            
            <button type="submit">필터 적용</button>
        </form>
    </div>
    
    {# 상품 그리드 #}
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {% for product in products %}
        <div class="product-card border rounded p-4">
            <img src="{{ product.image_url }}" alt="{{ product.title }}" class="w-full h-48 object-cover mb-4">
            <h3 class="font-bold mb-2">{{ product.title }}</h3>
            <p class="text-2xl font-bold text-red-600">
                {{ product.price|floatformat:0 }}원
                <span class="text-sm text-gray-500 line-through ml-2">
                    {{ product.original_price|floatformat:0 }}원
                </span>
            </p>
            <p class="text-sm text-green-600 mb-4">
                {{ product.discount_rate }}% 할인
            </p>
            
            {# 속성 표시 #}
            <div class="text-xs text-gray-600 mb-4">
                {% if product.down_ratio %}
                    <span class="badge">{{ product.down_ratio }}</span>
                {% endif %}
                {% if product.fill_power %}
                    <span class="badge">{{ product.fill_power }}FP</span>
                {% endif %}
                {% if product.fit %}
                    <span class="badge">{{ product.fit }}</span>
                {% endif %}
            </div>
            
            <a href="/api/out/?productId={{ product.id }}&subId=ewall-{{ brand.slug }}-{{ category.slug }}"
               target="_blank"
               class="block w-full bg-blue-600 text-white text-center py-2 rounded">
                구매하기
            </a>
        </div>
        {% endfor %}
    </div>
</div>
{% endblock %}
```

---

## 🧪 테스트 전략

### pytest 구조

```python
# tests/products/test_models.py
import pytest
from apps.products.models.categories import DownProduct

@pytest.mark.django_db
def test_down_product_creation():
    product = DownProduct.objects.create(
        id='test-001',
        brand=brand_fixture,
        category=category_fixture,
        title='Test Down Jacket',
        price=100000,
        original_price=150000,
        discount_rate=33.33,
        down_ratio='90-10',
        fill_power=800
    )
    
    assert product.down_ratio == '90-10'
    assert product.fill_power == 800


# tests/products/test_services.py
def test_attribute_extraction():
    text = "BrandA 거위털 다운 재킷 800FP 90/10 슬림핏"
    attrs = AttributeExtractor.extract(text, 'down')
    
    assert attrs['down_type'] == 'goose'
    assert attrs['down_ratio'] == '90-10'
    assert attrs['fill_power'] == 800
    assert attrs['fit'] == 'slim'


# tests/alerts/test_matcher.py
def test_alert_matching():
    product = DownProduct(
        price=89000,
        discount_rate=31,
        down_ratio='90-10',
        fill_power=800
    )
    
    conditions = {
        'priceBelow': 100000,
        'discountAtLeast': 30,
        'downRatio': '90-10'
    }
    
    matcher = AlertMatcher()
    assert matcher.matches(product, conditions) == True


# tests/smoke/test_api.py
def test_product_list_api(client):
    response = client.get('/api/products/branda/down/')
    
    assert response.status_code == 200
    assert 'products' in response.json()
    assert 'total' in response.json()
```

---

## 🚀 배포 설정

### Docker Compose

```yaml
# docker-compose.prod.yml
version: '3.8'

services:
  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ewall
      POSTGRES_USER: ewall
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data
    ports:
      - "5432:5432"
  
  redis:
    image: redis:7
    ports:
      - "6379:6379"
  
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
    volumes:
      - static_volume:/app/static
      - media_volume:/app/media
    ports:
      - "8000:8000"
    env_file:
      - .env
    depends_on:
      - db
      - redis
  
  celery_worker:
    build: .
    command: celery -A config worker -l info -Q default,high_priority,emails
    volumes:
      - ./:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis
  
  celery_beat:
    build: .
    command: celery -A config beat -l info
    volumes:
      - ./:/app
    env_file:
      - .env
    depends_on:
      - db
      - redis
  
  nginx:
    image: nginx:alpine
    volumes:
      - ./deployment/nginx/ewall.conf:/etc/nginx/conf.d/default.conf
      - static_volume:/static
      - media_volume:/media
    ports:
      - "80:80"
      - "443:443"
    depends_on:
      - web

volumes:
  postgres_data:
  static_volume:
  media_volume:
```

---

### GitHub Actions CI/CD

```yaml
# .github/workflows/ci.yml
name: CI/CD

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_DB: ewall_test
          POSTGRES_USER: postgres
          POSTGRES_PASSWORD: postgres
        ports:
          - 5432:5432
      
      redis:
        image: redis:7
        ports:
          - 6379:6379
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python 3.11
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          pip install -r requirements/testing.txt
      
      - name: Run migrations
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/ewall_test
        run: |
          python manage.py migrate --noinput
      
      - name: Run tests
        env:
          DATABASE_URL: postgresql://postgres:postgres@localhost:5432/ewall_test
          REDIS_URL: redis://localhost:6379/0
        run: |
          pytest --cov=apps --cov-report=xml --cov-report=html
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
      
      - name: Run smoke tests
        run: |
          python manage.py runserver 8000 &
          sleep 5
          pytest tests/smoke/ -v
```

---

## 📦 필수 패키지

```txt
# requirements/base.txt
Django==5.0
djangorestframework==3.14
django-filter==23.5
django-redis==5.4
psycopg2-binary==2.9
celery==5.3
redis==5.0

# 속성 검증
pydantic==2.5

# 로깅
python-json-logger==2.0

# 보안
django-cors-headers==4.3
django-ratelimit==4.1

# SEO
django-meta==2.3

# 환경변수
python-dotenv==1.0

# requirements/production.txt
-r base.txt
gunicorn==21.2
whitenoise==6.6
sentry-sdk==1.39

# requirements/testing.txt
-r base.txt
pytest==7.4
pytest-django==4.7
pytest-cov==4.1
factory-boy==3.3
```

---

## 🎯 마이그레이션 체크리스트

### Phase 1: 기반 구축 (Week 1-2)
- [ ] Django 프로젝트 초기화
- [ ] Models 정의 (7개 카테고리)
- [ ] PostgreSQL 마이그레이션
- [ ] Admin 패널 커스터마이징
- [ ] Redis 캐싱 설정

### Phase 2: 데이터 파이프라인 (Week 3-4)
- [ ] AttributeExtractor 구현
- [ ] ProductNormalizer 구현
- [ ] FeedFetcher 구현 (제휴사 API)
- [ ] Celery sync_feeds 태스크
- [ ] 실패 로깅 시스템

### Phase 3: API & 프론트엔드 (Week 5-6)
- [ ] DRF Serializers
- [ ] ProductListAPIView
- [ ] django-filter 설정
- [ ] 템플릿 뷰 (SSR)
- [ ] JSON-LD 생성

### Phase 4: 알림 시스템 (Week 7-8)
- [ ] Alert 모델
- [ ] EmailQueue 모델
- [ ] AlertMatcher 서비스
- [ ] check_price_changes 태스크
- [ ] send_queued_emails 태스크

### Phase 5: 분석 & 배포 (Week 9-10)
- [ ] Click 모델
- [ ] OutboundRedirectView
- [ ] pytest 테스트 (80% 커버리지)
- [ ] Docker 컨테이너화
- [ ] CI/CD 파이프라인

---

## 🔐 환경변수 (.env.example)

```bash
# Django
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=ewall.com,www.ewall.com

# Database
DATABASE_URL=postgresql://ewall:password@db:5432/ewall

# Redis
REDIS_URL=redis://redis:6379/0

# Celery
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# Email
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=noreply@ewall.com
EMAIL_HOST_PASSWORD=your-app-password

# 제휴사 API
COUPANG_ACCESS_KEY=your-key
COUPANG_SECRET_KEY=your-secret
LINKPRICE_API_KEY=your-key

# Monitoring
SENTRY_DSN=https://...

# CORS
CORS_ORIGINS=https://ewall.com,https://www.ewall.com
```

---

## 📊 성능 목표

| 지표 | 목표 |
|------|------|
| **API 응답 시간** | < 200ms (캐시 히트), < 500ms (캐시 미스) |
| **페이지 로드** | < 1초 (SSR) |
| **동시 사용자** | 10,000+ |
| **DB 쿼리** | < 5 queries/request |
| **캐시 히트율** | > 80% |
| **Celery 처리량** | 1,000 tasks/minute |
| **테스트 커버리지** | > 80% |

---

## ✅ 마이그레이션 완료 기준

- [ ] 모든 기능이 Django로 동작 (parity)
- [ ] 테스트 커버리지 80% 이상
- [ ] CI/CD 파이프라인 통과
- [ ] 프로덕션 배포 완료
- [ ] 모니터링 (Sentry, Prometheus) 설정
- [ ] 문서화 완료

---

## 📞 지원 정보

- **원본 프로젝트**: https://github.com/miin1736/volunteer
- **GitHub Issues**: 위 링크 참조
- **기술 스택**: Django 5.0, DRF 3.14, Celery 5.3, PostgreSQL 15, Redis 7

---

**마지막 업데이트**: 2025-11-21  
**버전**: 1.0.0
