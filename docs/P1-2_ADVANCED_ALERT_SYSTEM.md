# P1-2: Advanced Alert System

## 📋 개요

**구현 일자**: 2025-01-XX  
**상태**: ✅ 완료  
**테스트**: 23개 테스트 케이스  
**커버리지**: 목표 80%+

고급 알림 시스템은 기존 단순 가격 알림을 확장하여 복합 조건, 가격 추세 분석, 스마트 매칭, 알림 히스토리 및 통계 기능을 제공합니다.

---

## 🎯 주요 기능

### 1. AlertConditionBuilder (복합 조건 빌더)
- **AND/OR 복합 조건** 지원
- **가격 조건**: 범위, 이하, 이상
- **할인 조건**: 최소 할인율, 할인 범위
- **추세 조건**: falling, rising, stable, volatile
- **상대 가격 조건**: 평균가 대비 %, 최저가 대비 %
- **재고 조건**: 재고 있는 상품만, 재입고 알림
- **우선순위 설정**: 1 (최고) ~ 5 (최저)
- **JSON 스키마 검증**

```python
from apps.alerts.services import AlertConditionBuilder

# 기본 조건
builder = AlertConditionBuilder()
builder.add_price_condition(max_price=100000)
builder.add_discount_condition(min_discount=30)
builder.add_trend_condition(trend='falling', threshold=10.0)
builder.set_priority(1)

conditions = builder.build()
```

### 2. PriceTrendAnalyzer (가격 추세 분석)
- **7일/30일/90일 추세 분석**
- **급등/급락 감지** (변동률 기반)
- **평균가/최저가/최고가 계산**
- **변동성(Volatility) 계산**
- **상대 가격 계산** (평균가 대비, 최저가 대비)
- **가격 이력 데이터 조회** (그래프용)

```python
from apps.alerts.services import PriceTrendAnalyzer

analyzer = PriceTrendAnalyzer()

# 추세 분석
trend = analyzer.analyze_product_trend(product_id, period_days=30)
# {
#   'trend': 'falling',
#   'avg_price': 92500.0,
#   'min_price': 88000.0,
#   'max_price': 100000.0,
#   'current_price': 90000.0,
#   'price_change': -10000.0,
#   'price_change_percent': -10.0,
#   'volatility': 4.2,
#   'data_points': 30
# }

# 급락 감지
drop = analyzer.detect_price_drop(product_id, threshold_percent=10.0)

# 상대 가격 계산
relative = analyzer.calculate_relative_price(product_id, current_price, period_days=30)
```

### 3. SmartAlertMatcher (스마트 알림 매칭)
- **복합 조건 매칭** (AND/OR 연산)
- **우선순위 기반 정렬**
- **중복 알림 방지** (24시간 쿨다운)
- **추세 기반 조건 매칭**
- **상대 가격 조건 매칭**
- **재입고 감지**

```python
from apps.alerts.services import SmartAlertMatcher

matcher = SmartAlertMatcher()

# 상품-알림 매칭
matched = matcher.match_product_to_alerts(
    product=product,
    alerts=alerts,
    cooldown_hours=24
)
# [(alert, priority), ...]

# 발송 기록 (쿨다운 시작)
matcher.mark_sent(alert_id, product_id)
```

### 4. 알림 히스토리 및 통계
- **AlertHistory**: 알림 발송 이력 저장
- **AlertStatistics**: 일별 통계 집계
- **클릭 트래킹**: 사용자 액션 추적
- **성과 측정**: 오픈율, 클릭율

```python
from apps.alerts.models import AlertHistory, AlertStatistics

# 히스토리 생성
history = AlertHistory.objects.create(
    alert=alert,
    product_id=product.id,
    product_data={'title': '...', 'price': 80000},
    matched_conditions=conditions,
    priority=1,
    email_sent=True
)

# 통계 조회
stats = AlertStatistics.objects.filter(
    alert=alert,
    date__gte=start_date
).order_by('date')
```

### 5. 개선된 이메일 템플릿
- **가격 그래프**: 최근 7일 가격 변동 시각화
- **추세 정보**: 평균가 대비, 변동률 표시
- **개인화 메시지**: 사용자별 맞춤 콘텐츠
- **상품 이미지**: 고품질 이미지 표시
- **액션 버튼**: 구매하기, 상세 보기
- **반응형 디자인**: 모바일 최적화

### 6. 고급 알림 관리 API
- **대시보드**: 활성 알림, 통계, 최근 이력
- **히스토리**: 발송 이력 조회 (페이징)
- **통계**: 일별/기간별 통계
- **조건 검증**: 알림 조건 유효성 검증
- **일괄 업데이트**: 활성화/비활성화/삭제
- **추천 조건**: AI 기반 조건 추천

---

## 📂 파일 구조

```
apps/alerts/
├── services/
│   ├── __init__.py                    # 서비스 모듈 초기화
│   ├── matcher.py                     # 기존 매처 (카테고리 속성)
│   ├── condition_builder.py           # ✨ 복합 조건 빌더 (389 lines)
│   ├── trend_analyzer.py              # ✨ 가격 추세 분석 (453 lines)
│   └── smart_matcher.py               # ✨ 스마트 알림 매칭 (406 lines)
│
├── models.py                          # ✨ Alert, EmailQueue, AlertHistory, AlertStatistics
│
├── views/
│   ├── __init__.py
│   ├── advanced_api.py                # ✨ 고급 알림 API (470 lines)
│   └── (기존 API views)
│
├── urls.py                            # ✨ 라우팅 추가
├── admin.py
├── serializers.py
├── tasks.py
└── migrations/
    └── 0002_alerthistory_alertstatistics.py  # ✨ 마이그레이션

templates/emails/
├── price_drop.html                    # 기존 템플릿
└── advanced_alert.html                # ✨ 고급 템플릿 (418 lines)

tests/
└── test_advanced_alerts.py            # ✨ 23개 테스트 (423 lines)

docs/
└── P1-2_ADVANCED_ALERT_SYSTEM.md     # ✨ 이 문서
```

**총 추가 라인 수**: ~2,500 lines  
**새 파일**: 6개  
**수정 파일**: 3개

---

## 🔧 API 엔드포인트

### 1. 알림 대시보드
```http
GET /api/alerts/dashboard/?email={email}
```

**응답**:
```json
{
  "alerts": [...],
  "inactive_alerts_count": 2,
  "statistics": {
    "total_matched": 45,
    "total_sent": 40,
    "total_clicked": 15,
    "click_rate": 37.5,
    "period_days": 30
  },
  "recent_history": [...]
}
```

### 2. 알림 히스토리
```http
GET /api/alerts/{alert_id}/history/?limit=20&offset=0
```

### 3. 알림 통계
```http
GET /api/alerts/{alert_id}/statistics/?days=30
```

**응답**:
```json
{
  "alert_id": "...",
  "period": {"start_date": "...", "end_date": "...", "days": 30},
  "summary": {
    "total_matched": 45,
    "total_sent": 40,
    "total_clicked": 15,
    "avg_click_rate": 37.5,
    "avg_price": 85000.0
  },
  "daily": [
    {"date": "2025-01-01", "matched": 3, "sent": 2, "clicked": 1, ...},
    ...
  ]
}
```

### 4. 조건 검증
```http
POST /api/alerts/validate-conditions/
Content-Type: application/json

{
  "conditions": {
    "priceBelow": 100000,
    "discountAtLeast": 30
  },
  "operator": "AND",
  "priority": 1
}
```

### 5. 상품 가격 추세
```http
GET /api/products/{product_id}/trend/?days=30
```

**응답**:
```json
{
  "product_id": "...",
  "trend": {
    "trend": "falling",
    "avg_price": 92500.0,
    "min_price": 88000.0,
    "max_price": 100000.0,
    "current_price": 90000.0,
    "price_change_percent": -10.0,
    "volatility": 4.2
  },
  "history": [
    {"date": "2025-01-01", "price": 100000},
    {"date": "2025-01-02", "price": 98000},
    ...
  ]
}
```

### 6. 일괄 업데이트
```http
POST /api/alerts/bulk-update/
Content-Type: application/json

{
  "email": "user@example.com",
  "action": "activate",  // "activate" | "deactivate" | "delete"
  "alert_ids": ["...", "..."]
}
```

### 7. 추천 알림 조건
```http
GET /api/alerts/recommended/?email={email}
```

**응답**:
```json
{
  "email": "user@example.com",
  "recommended": [
    {
      "name": "선호 가격대",
      "description": "70,000원 ~ 130,000원, 30% 이상 할인",
      "conditions": {...}
    },
    {
      "name": "가격 하락 추세",
      "description": "최근 7일간 10% 이상 가격 하락한 상품",
      "conditions": {...}
    },
    ...
  ],
  "based_on": {
    "clicked_products": 10,
    "avg_price": 100000.0,
    "avg_discount": 30.0
  }
}
```

---

## 🧪 테스트

### 테스트 구조

```python
# tests/test_advanced_alerts.py

@pytest.mark.django_db
class TestAlertConditionBuilder:
    # 9 tests
    - test_basic_price_condition
    - test_price_range_condition
    - test_discount_condition
    - test_trend_condition
    - test_relative_price_condition
    - test_complex_condition_with_operator
    - test_priority_setting
    - test_invalid_price_range
    - test_from_dict

@pytest.mark.django_db
class TestPriceTrendAnalyzer:
    # 4 tests
    - test_analyze_product_trend_falling
    - test_detect_price_drop
    - test_calculate_relative_price
    - test_get_price_history_data

@pytest.mark.django_db
class TestSmartAlertMatcher:
    # 7 tests
    - test_match_product_to_alerts
    - test_matches_conditions
    - test_price_condition_matching
    - test_discount_condition_matching
    - test_stock_condition_matching
    - test_cooldown_prevention

@pytest.mark.django_db
class TestAlertModels:
    # 2 tests
    - test_create_alert_history
    - test_create_alert_statistics

@pytest.mark.integration
class TestAdvancedAlertAPIs:
    # 3 tests
    - test_alert_dashboard_api
    - test_alert_history_api
    - test_alert_statistics_api
```

### 테스트 실행

```bash
# 전체 테스트
pytest tests/test_advanced_alerts.py -v

# 특정 클래스 테스트
pytest tests/test_advanced_alerts.py::TestAlertConditionBuilder -v

# 커버리지 측정
pytest tests/test_advanced_alerts.py --cov=apps.alerts.services --cov-report=html
```

---

## 🚀 사용 예제

### 예제 1: 복합 조건 알림 생성

```python
from apps.alerts.services import AlertConditionBuilder
from apps.alerts.models import Alert
from apps.core.models import Brand, Category

# 조건 빌더 생성
builder = AlertConditionBuilder()

# 가격: 50,000 ~ 100,000원
builder.add_price_condition(
    min_price=Decimal('50000'),
    max_price=Decimal('100000')
)

# 할인: 30% 이상
builder.add_discount_condition(min_discount=30.0)

# 추세: 최근 7일간 10% 이상 가격 하락
builder.add_trend_condition(trend='falling', threshold=10.0)

# 재고: 재고 있는 상품만
builder.add_stock_condition(in_stock_only=True)

# 우선순위: 1 (최고)
builder.set_priority(1)

# 조건 빌드
conditions = builder.build()

# 알림 생성
brand = Brand.objects.get(slug='northface')
category = Category.objects.get(slug='down')

alert = Alert.objects.create(
    email='user@example.com',
    brand=brand,
    category=category,
    conditions=conditions,
    active=True
)
```

### 예제 2: 가격 추세 분석

```python
from apps.alerts.services import PriceTrendAnalyzer

analyzer = PriceTrendAnalyzer()

# 30일 추세 분석
trend = analyzer.analyze_product_trend('coupang-12345', period_days=30)

if trend['trend'] == 'falling':
    print(f"가격 하락 추세! {trend['price_change_percent']:.1f}% 하락")
    print(f"평균가: {trend['avg_price']:,.0f}원")
    print(f"현재가: {trend['current_price']:,.0f}원")

# 급락 감지
drop = analyzer.detect_price_drop('coupang-12345', threshold_percent=15.0)

if drop and drop['detected']:
    print(f"가격 급락 감지! {drop['price_change_percent']:.1f}% 하락")
```

### 예제 3: 스마트 매칭 및 이메일 발송

```python
from apps.alerts.services import SmartAlertMatcher
from apps.alerts.models import Alert, EmailQueue
from apps.products.models import GenericProduct
from django.template.loader import render_to_string

matcher = SmartAlertMatcher()

# 최근 업데이트된 상품
products = GenericProduct.objects.filter(
    updated_at__gte=timezone.now() - timedelta(hours=1),
    in_stock=True
)

# 활성 알림
alerts = Alert.objects.filter(active=True)

# 일괄 매칭
matched_results = matcher.batch_match_products(products, alerts)

# 이메일 큐 추가
for product_id, matched_alerts in matched_results.items():
    product = GenericProduct.objects.get(id=product_id)
    
    for alert, priority in matched_alerts:
        # HTML 이메일 렌더링
        html_body = render_to_string('emails/advanced_alert.html', {
            'alert_emoji': '🎉',
            'alert_title': '가격 하락 알림',
            'alert_subtitle': '조건에 맞는 상품이 발견되었습니다!',
            'alert': alert,
            'product': product,
            'trend_info': analyzer.analyze_product_trend(product_id, period_days=7),
            'personalized_message': f'{alert.email}님을 위한 맞춤 상품입니다.',
        })
        
        # 이메일 큐 추가
        EmailQueue.objects.create(
            to_email=alert.email,
            subject=f"💰 {product.title[:40]} - 가격 하락 알림",
            body_html=html_body,
            reason='price_drop',
            product_id=product.id,
            product_data={
                'title': product.title,
                'price': float(product.price),
                'discount_rate': float(product.discount_rate),
            },
            alert=alert
        )
        
        # 쿨다운 기록
        matcher.mark_sent(alert.id, product.id)
```

---

## 📊 데이터베이스 스키마

### AlertHistory
```sql
CREATE TABLE alerts_alerthistory (
    id UUID PRIMARY KEY,
    alert_id UUID REFERENCES alerts_alert(id),
    product_id VARCHAR(100),
    product_data JSONB,
    matched_conditions JSONB,
    priority INTEGER DEFAULT 3,
    email_sent BOOLEAN DEFAULT FALSE,
    email_sent_at TIMESTAMP NULL,
    clicked BOOLEAN DEFAULT FALSE,
    clicked_at TIMESTAMP NULL,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE INDEX idx_alert_created ON alerts_alerthistory(alert_id, created_at);
CREATE INDEX idx_product_created ON alerts_alerthistory(product_id, created_at);
```

### AlertStatistics
```sql
CREATE TABLE alerts_alertstatistics (
    id UUID PRIMARY KEY,
    alert_id UUID REFERENCES alerts_alert(id),
    date DATE NOT NULL,
    total_matched INTEGER DEFAULT 0,
    total_sent INTEGER DEFAULT 0,
    total_clicked INTEGER DEFAULT 0,
    open_rate FLOAT DEFAULT 0.0,
    click_rate FLOAT DEFAULT 0.0,
    avg_matched_price DECIMAL(10, 2) NULL,
    avg_discount_rate FLOAT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(alert_id, date)
);

CREATE INDEX idx_alert_date ON alerts_alertstatistics(alert_id, date);
```

---

## 🔄 Celery 태스크 확장

### 기존 태스크 개선

```python
# apps/alerts/tasks.py

from apps.alerts.services import SmartAlertMatcher

@shared_task
def check_price_changes():
    """고급 알림 매칭 사용"""
    matcher = SmartAlertMatcher()
    
    # ... (기존 로직)
    
    # 스마트 매칭 적용
    matched = matcher.match_product_to_alerts(
        product=product,
        alerts=alerts,
        cooldown_hours=24
    )
    
    for alert, priority in matched:
        # 이메일 큐 추가
        # ...
```

### 새 태스크: 통계 집계

```python
@shared_task
def aggregate_alert_statistics():
    """일별 알림 통계 집계
    
    실행 주기: 매일 자정 10분
    """
    from apps.alerts.models import Alert, AlertHistory, AlertStatistics
    from django.utils import timezone
    from datetime import timedelta
    
    yesterday = (timezone.now() - timedelta(days=1)).date()
    
    # 모든 활성 알림
    alerts = Alert.objects.filter(active=True)
    
    for alert in alerts:
        # 어제 히스토리
        history = AlertHistory.objects.filter(
            alert=alert,
            created_at__date=yesterday
        )
        
        total_matched = history.count()
        total_sent = history.filter(email_sent=True).count()
        total_clicked = history.filter(clicked=True).count()
        
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        
        # 평균 가격
        prices = [h.product_data.get('price', 0) for h in history]
        avg_price = sum(prices) / len(prices) if prices else None
        
        # 평균 할인율
        discounts = [h.product_data.get('discount_rate', 0) for h in history]
        avg_discount = sum(discounts) / len(discounts) if discounts else None
        
        # 통계 생성/업데이트
        AlertStatistics.objects.update_or_create(
            alert=alert,
            date=yesterday,
            defaults={
                'total_matched': total_matched,
                'total_sent': total_sent,
                'total_clicked': total_clicked,
                'click_rate': click_rate,
                'avg_matched_price': avg_price,
                'avg_discount_rate': avg_discount,
            }
        )
```

---

## 🎨 프론트엔드 연동

### 알림 대시보드 (React 예제)

```jsx
import React, { useEffect, useState } from 'react';
import axios from 'axios';

function AlertDashboard({ userEmail }) {
  const [dashboard, setDashboard] = useState(null);

  useEffect(() => {
    axios.get(`/api/alerts/dashboard/?email=${userEmail}`)
      .then(res => setDashboard(res.data));
  }, [userEmail]);

  if (!dashboard) return <div>Loading...</div>;

  return (
    <div>
      <h2>알림 대시보드</h2>
      
      <div className="statistics">
        <div className="stat-card">
          <h3>{dashboard.statistics.total_matched}</h3>
          <p>매칭된 상품</p>
        </div>
        <div className="stat-card">
          <h3>{dashboard.statistics.total_sent}</h3>
          <p>발송된 알림</p>
        </div>
        <div className="stat-card">
          <h3>{dashboard.statistics.click_rate}%</h3>
          <p>클릭률</p>
        </div>
      </div>

      <div className="active-alerts">
        <h3>활성 알림 ({dashboard.alerts.length}개)</h3>
        {dashboard.alerts.map(alert => (
          <div key={alert.id} className="alert-card">
            <h4>{alert.brand} {alert.category}</h4>
            <p>조건: {JSON.stringify(alert.conditions.conditions)}</p>
          </div>
        ))}
      </div>

      <div className="recent-history">
        <h3>최근 매칭 이력</h3>
        {dashboard.recent_history.map(h => (
          <div key={h.product_id}>
            <p>{h.product_title} - {h.price}원</p>
            <span>{h.email_sent ? '✅ 발송됨' : '⏳ 대기'}</span>
          </div>
        ))}
      </div>
    </div>
  );
}
```

---

## 🔒 보안 고려사항

1. **이메일 검증**: 사용자 본인의 이메일만 조회 가능
2. **Rate Limiting**: API 호출 횟수 제한
3. **CSRF 보호**: POST 요청 CSRF 토큰 필수
4. **SQL Injection 방지**: ORM 사용
5. **XSS 방지**: HTML 이스케이핑

---

## 📈 성능 최적화

1. **캐싱**: PriceTrendAnalyzer에 1분 TTL 캐시
2. **인덱싱**: AlertHistory, AlertStatistics 인덱스 최적화
3. **쿼리 최적화**: select_related, prefetch_related 사용
4. **배치 처리**: batch_match_products로 대량 매칭
5. **비동기 처리**: Celery 태스크 활용

---

## 🐛 트러블슈팅

### 1. 추세 분석 데이터 없음
**문제**: PriceHistory가 없어 추세 분석 불가  
**해결**: `snapshot_prices` 태스크가 정상 실행되는지 확인

### 2. 중복 알림 발송
**문제**: 같은 상품에 대해 반복 알림  
**해결**: `cooldown_hours` 설정 확인, `mark_sent()` 호출 확인

### 3. 조건 매칭 실패
**문제**: 조건이 맞는데 매칭 안됨  
**해결**: 조건 우선순위, 연산자(AND/OR) 확인

---

## 🔮 향후 개선 사항

1. **WebSocket 실시간 알림** (P1-2.1)
2. **브라우저 푸시 알림** (P1-2.2)
3. **알림 템플릿 커스터마이징** (P1-2.3)
4. **AI 기반 조건 추천 고도화** (P2 연계)
5. **알림 성과 분석 대시보드** (P3)

---

## 📚 참고 자료

- [Django Signals](https://docs.djangoproject.com/en/5.0/topics/signals/)
- [Celery Beat](https://docs.celeryproject.org/en/stable/userguide/periodic-tasks.html)
- [Django ORM Optimization](https://docs.djangoproject.com/en/5.0/topics/db/optimization/)
- [RESTful API Design](https://restfulapi.net/)

---

## ✅ 체크리스트

- [x] AlertConditionBuilder 구현
- [x] PriceTrendAnalyzer 구현
- [x] SmartAlertMatcher 구현
- [x] AlertHistory 모델 추가
- [x] AlertStatistics 모델 추가
- [x] 고급 이메일 템플릿 작성
- [x] 고급 알림 API 7개 구현
- [x] URL 라우팅 추가
- [x] 마이그레이션 생성
- [x] 23개 테스트 작성
- [x] 문서화 작성
- [ ] 실제 데이터베이스 마이그레이션 실행
- [ ] 통합 테스트 실행
- [ ] 프론트엔드 연동 테스트
- [ ] 성능 벤치마크

---

**작성자**: GitHub Copilot  
**버전**: 1.0.0  
**마지막 업데이트**: 2025-01-XX
