# E-wall 이월상품 수집 시작 가이드

## 🚀 즉시 시작: 네이버 쇼핑 API

### 1단계: API 키 발급 (5분)

#### 1. 네이버 개발자센터 가입
```
https://developers.naver.com
```

#### 2. 애플리케이션 등록
```
1. 상단 메뉴 "Application" → "애플리케이션 등록"
2. 애플리케이션 이름: "E-wall 이월상품 검색"
3. 사용 API: "검색" 체크
4. 비로그인 오픈 API 서비스 환경:
   - WEB 설정: http://localhost:8000
5. 등록 클릭
```

#### 3. Client ID/Secret 확인
```
등록 완료 후 표시되는:
- Client ID: abc123...
- Client Secret: xyz789...
```

---

### 2단계: 환경변수 설정 (1분)

#### `.env.development` 파일에 추가
```bash
# Naver Shopping API
NAVER_CLIENT_ID=your-client-id-here
NAVER_CLIENT_SECRET=your-client-secret-here
```

#### `.env.production` 파일에도 동일하게 추가

---

### 3단계: 테스트 실행 (2분)

```powershell
# Django shell 실행
python manage.py shell
```

```python
# 네이버 쇼핑 API 테스트
from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler

crawler = NaverShoppingCrawler()

# 이월상품 검색 테스트
products = crawler.search_outlet_products(
    brands=['노스페이스', '파타고니아'],
    limit_per_brand=20
)

print(f"수집된 상품: {len(products)}개")

# 첫 5개 상품 확인
for p in products[:5]:
    print(f"{p['title']} - {p['price']:,}원 ({p['discount_rate']}% 할인)")
```

**예상 결과:**
```
수집된 상품: 156개
노스페이스 NEW 눕시 다운 자켓 - 198,000원 (40% 할인)
파타고니아 다운 스웨터 후디 - 265,000원 (35% 할인)
...
```

---

### 4단계: 데이터베이스 저장 (5분)

```python
# Django shell에서 계속
from apps.products.tasks import crawl_multi_platform

# 실제 상품 크롤링 및 DB 저장
result = crawl_multi_platform.apply(
    kwargs={
        'keywords': [
            '노스페이스 이월',
            '파타고니아 아울렛',
            '아크테릭스 세일'
        ],
        'platforms': ['naver']
    }
)

print(result)
# {'created': 145, 'updated': 0, 'errors': 2}
```

---

### 5단계: 관리자 페이지 확인

```powershell
# 개발 서버 실행
python manage.py runserver
```

```
브라우저에서:
http://localhost:8000/admin/products/

→ 실제 상품들이 저장되어 있음!
```

---

## 🎯 자동 크롤링 설정

### Celery 태스크 활성화

```powershell
# Celery Worker 실행
celery -A config worker -l info --pool=solo

# Celery Beat 실행 (스케줄러)
celery -A config beat -l info
```

**자동 실행 스케줄:**
- **4시간마다**: 이월상품 크롤링
- **매일 자정**: 가격 스냅샷
- **1시간마다**: 가격 변동 감지

---

## 📊 수집 결과 확인

### 현재 상품 수 확인
```python
from apps.products.models import *

# 전체 상품 수
print(f"총 상품: {GenericProduct.objects.count()}개")

# 카테고리별
print(f"다운: {DownProduct.objects.count()}개")
print(f"슬랙스: {SlacksProduct.objects.count()}개")

# 할인율 30% 이상
from django.db.models import Q
outlet_products = GenericProduct.objects.filter(discount_rate__gte=30)
print(f"이월상품: {outlet_products.count()}개")

# 브랜드별
from apps.core.models import Brand
for brand in Brand.objects.all()[:5]:
    count = GenericProduct.objects.filter(brand=brand).count()
    print(f"{brand.name}: {count}개")
```

---

## 🔥 쿠팡 파트너스 추가 (선택, 1주일)

### 1. 쿠팡 파트너스 가입
```
https://partners.coupang.com
```

### 2. 웹사이트 정보 입력
```
- 웹사이트 URL: http://yourdomain.com (또는 블로그)
- 웹사이트 설명: "브랜드 이월상품 가격 비교 서비스"
- 카테고리: 쇼핑/패션
```

### 3. 승인 대기 (1-3일)

### 4. API 키 발급 후 설정
```bash
# .env 파일
COUPANG_ACCESS_KEY=your-access-key
COUPANG_SECRET_KEY=your-secret-key
```

### 5. 쿠팡 크롤러 활성화
```python
# Django shell
from apps.products.services.search_aggregator import SearchAggregator

# 쿠팡 포함 검색
agg = SearchAggregator(use_official_apis=True)
result = agg.search('노스페이스 이월', platforms=['naver', 'coupang'])

print(f"네이버: {result['platforms'].get('naver', 0)}개")
print(f"쿠팡: {result['platforms'].get('coupang', 0)}개")
```

---

## 💰 수익화 팁

### 1. 딥링크 자동 생성 (쿠팡)
```python
# 모든 쿠팡 상품에 자동으로 제휴 링크 적용
# 사용자가 클릭 → 구매 시 수수료 자동 발생 (1.5-9%)
```

### 2. 수익 예측
```
월 방문자 1,000명
클릭율 5% = 50클릭
구매 전환율 10% = 5건
평균 구매액 200,000원
평균 수수료율 3%

= 200,000 × 5 × 0.03 = 30,000원/월
```

### 3. 수익 확대
- 방문자 10,000명 → 월 300,000원
- 방문자 100,000명 → 월 3,000,000원

---

## 🎁 보너스: 이월상품 특화 키워드

```python
# config/outlet_keywords.py
OUTLET_KEYWORDS = {
    '브랜드': [
        '노스페이스 이월', '파타고니아 아울렛', '아크테릭스 세일',
        '밀레 이월상품', '마무트 할인', '코오롱스포츠 이월',
        '네파 아울렛', '블랙야크 세일', '아이더 이월'
    ],
    '카테고리': [
        '다운점퍼 이월', '패딩 아울렛', '등산복 세일',
        '아웃도어 이월상품', '겨울옷 할인', '기능성의류 아울렛'
    ],
    '시즌': [
        '작년 다운', '재고처리 패딩', '구형 모델',
        '시즌오프', '겨울 이월'
    ],
    '할인': [
        '30% 이상', '반값', '파격세일', 
        '특가', '최저가', '재고소진'
    ]
}

# 사용
from apps.products.tasks import crawl_multi_platform

crawl_multi_platform.delay(
    keywords=OUTLET_KEYWORDS['브랜드'] + OUTLET_KEYWORDS['카테고리']
)
```

---

## 🆘 문제 해결

### Q: "Client ID/Secret이 잘못되었습니다"
```
→ .env 파일 재확인
→ 따옴표 없이 입력 (NAVER_CLIENT_ID=abc123)
→ 서버 재시작 (python manage.py runserver)
```

### Q: "상품이 0개 수집됨"
```python
# 크롤러 직접 테스트
from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler

crawler = NaverShoppingCrawler()
print(f"Client ID: {crawler.client_id[:10]}...")  # 앞 10자만 확인
print(f"Secret: {crawler.client_secret[:10]}...")

# 단순 검색 테스트
result = crawler.search('노스페이스', limit=10)
print(f"결과: {len(result)}개")
```

### Q: "API 할당량 초과"
```
네이버: 일 25,000건 (무료)
→ 키워드 수 조절
→ 크롤링 주기 조정 (4시간 → 6시간)
```

---

## ✅ 성공 체크리스트

- [ ] 네이버 개발자센터 가입
- [ ] Client ID/Secret 발급
- [ ] .env 파일 설정
- [ ] 크롤러 테스트 성공
- [ ] DB에 상품 저장 확인
- [ ] Celery 자동 크롤링 설정
- [ ] 관리자 페이지에서 상품 확인
- [ ] 웹사이트에서 상품 목록 표시

---

## 🚀 다음 단계

1. **쿠팡 파트너스 승인 대기**
2. **이월상품 전용 페이지 제작**
3. **가격 알림 기능 테스트**
4. **클라우드 배포 준비**
5. **SEO 최적화 (구글 검색 노출)**

축하합니다! 이제 실제 이월상품 데이터로 서비스할 수 있습니다! 🎉
