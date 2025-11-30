# 쿠팡 파트너스 신청 가이드

## 📋 사전 준비 사항

쿠팡 파트너스는 **웹사이트/블로그가 필요**합니다. 아래 중 하나를 준비하세요:

### 옵션 A: 간단한 소개 페이지 (추천)
```
Notion 무료 페이지:
1. https://notion.so 가입
2. 새 페이지 생성
3. E-wall 서비스 소개 작성
   - 서비스 이름: E-wall
   - 설명: 브랜드 이월상품 가격 비교 플랫폼
   - 카테고리: 패션, 아웃도어
4. 페이지 공개 설정
5. 링크 복사

예시: https://your-notion.notion.site/E-wall-123abc
```

### 옵션 B: GitHub Pages (무료 도메인)
```
1. GitHub 저장소 Settings
2. Pages 활성화
3. README.md에 서비스 소개 작성
4. https://yourusername.github.io/ewall-django

(쿠팡이 승인할 가능성 높음)
```

### 옵션 C: 실제 도메인 (가장 확실)
```
도메인 구매 (연 1-2만원):
- Namecheap: 약 $10/년
- 가비아: 약 15,000원/년

→ 승인율 거의 100%
```

---

## 1단계: 쿠팡 파트너스 가입

### 1-1. 회원가입
```
https://partners.coupang.com
```

### 1-2. 로그인 후 "제휴 신청" 클릭

### 1-3. 웹사이트 정보 입력
```
웹사이트 URL: 
  - Notion 페이지 URL 또는
  - GitHub Pages URL 또는
  - 실제 도메인

웹사이트 이름: E-wall

웹사이트 설명:
"브랜드 이월상품을 한눈에 비교할 수 있는 가격 비교 플랫폼입니다. 
노스페이스, 파타고니아 등 국내외 프리미엄 브랜드의 이월상품 정보를 
실시간으로 제공하여 소비자가 합리적인 구매를 할 수 있도록 돕습니다."

카테고리: 쇼핑/패션

월 예상 방문자: 1,000명 (실제 론칭 전이면 예상치 입력)

트래픽 소스: 검색엔진, 소셜미디어
```

### 1-4. 제출 후 대기
```
승인 소요 시간: 1-3일 (평일 기준)
승인 메일: partners@coupang.com에서 발송
```

---

## 2단계: 승인 후 API 키 발급

### 2-1. 승인 메일 확인

### 2-2. 파트너스 센터 로그인
```
https://partners.coupang.com
```

### 2-3. "도구" → "API 설정" 메뉴

### 2-4. API 키 발급
```
Access Key: (생성 클릭)
Secret Key: (자동 생성)

⚠️ Secret Key는 최초 1회만 표시되므로 반드시 복사!
```

---

## 3단계: 환경변수 설정

### `.env.development` 파일에 추가
```env
# Coupang Partners API
COUPANG_ACCESS_KEY=발급받은_Access_Key
COUPANG_SECRET_KEY=발급받은_Secret_Key
```

### `.env.production` 파일에도 동일하게 추가

---

## 4단계: 테스트 실행

```powershell
# Django shell
python manage.py shell
```

```python
from apps.products.services.crawlers.coupang_partners_crawler import CoupangPartnersCrawler

crawler = CoupangPartnersCrawler()

# 검색 테스트
products = crawler.search('노스페이스 다운', limit=10)
print(f"검색 결과: {len(products)}개")

for p in products[:3]:
    print(f"{p['title'][:50]}")
    print(f"가격: {p['price']:,}원 (할인: {p['discount_rate']}%)")
    print(f"딥링크: {p['product_url'][:50]}...")
    print()

# 이월상품 검색
outlet = crawler.search_outlet_products(['노스페이스'], min_discount=30)
print(f"\n이월상품(30% 이상 할인): {len(outlet)}개")
```

---

## 5단계: 네이버 + 쿠팡 통합 검색

```python
from apps.products.services.search_aggregator import SearchAggregator

# 공식 API 사용
agg = SearchAggregator(use_official_apis=True)

# 멀티 플랫폼 검색
result = agg.search(
    keyword='노스페이스 이월',
    platforms=['naver', 'coupang'],
    limit=50
)

print(f"총 {result['total']}개 상품")
print(f"네이버: {result['platforms'].get('naver', 0)}개")
print(f"쿠팡: {result['platforms'].get('coupang', 0)}개")

# 상위 5개 출력
for p in result['products'][:5]:
    print(f"[{p['platform']}] {p['title'][:40]} - {p['price']:,}원")
```

---

## 6단계: 자동 크롤링 설정

```python
# 통합 크롤링 실행
from apps.products.tasks import crawl_multi_platform

result = crawl_multi_platform.apply(
    kwargs={
        'keywords': [
            '노스페이스 이월',
            '파타고니아 아울렛',
            '아크테릭스 세일',
            '밀레 이월상품',
            '코오롱스포츠 할인'
        ],
        'platforms': ['naver', 'coupang']  # 양쪽 모두 검색
    }
)

print(f"생성: {result['created']}개")
print(f"업데이트: {result['updated']}개")
```

---

## 7단계: Celery 자동 크롤링 활성화

```powershell
# Terminal 1: Celery Worker
celery -A config worker -l info --pool=solo

# Terminal 2: Celery Beat (스케줄러)
celery -A config beat -l info

# Terminal 3: Django 서버
python manage.py runserver
```

**자동 크롤링 스케줄:**
- 4시간마다: 네이버 + 쿠팡 이월상품 검색
- 매일 자정: 가격 스냅샷
- 1시간마다: 가격 변동 확인

---

## 💰 수익 확인

### 쿠팡 파트너스 수익 확인
```
1. https://partners.coupang.com 로그인
2. "리포트" → "실적 리포트"
3. 클릭 수, 주문 수, 수수료 확인
```

### 딥링크 작동 확인
```python
from apps.products.services.crawlers.coupang_partners_crawler import CoupangPartnersCrawler

crawler = CoupangPartnersCrawler()

# 일반 URL을 제휴 딥링크로 변환
original_url = "https://www.coupang.com/vp/products/12345"
deeplink = crawler.generate_deeplink(original_url, sub_id='ewall-test')

print(f"딥링크: {deeplink}")
# → https://link.coupang.com/a/bXXXXX
# 이 링크로 구매 시 수수료 발생!
```

---

## ✅ 최종 체크리스트

### 네이버 API
- [ ] 네이버 개발자센터 API 키 발급
- [ ] .env 파일 설정
- [ ] 검색 테스트 성공
- [ ] DB 저장 확인

### 쿠팡 파트너스
- [ ] 웹사이트/블로그 준비
- [ ] 쿠팡 파트너스 가입
- [ ] 제휴 신청 제출
- [ ] 승인 대기 (1-3일)
- [ ] API 키 발급
- [ ] .env 파일 설정
- [ ] 검색 테스트 성공
- [ ] 딥링크 생성 확인

### 통합 운영
- [ ] 네이버 + 쿠팡 동시 검색 테스트
- [ ] Celery 자동 크롤링 설정
- [ ] 관리자 페이지에서 상품 확인
- [ ] 웹사이트에서 상품 목록 표시
- [ ] 가격 알림 기능 테스트

---

## 📊 예상 결과

### 데이터 규모
```
네이버 API: 일 25,000건 무료
쿠팡 API: 무제한

예상 수집 상품 수:
- 1일차: 500-1,000개
- 1주일차: 3,000-5,000개
- 1개월차: 10,000-20,000개
```

### 수익 예상 (쿠팡)
```
월 방문자 1,000명 가정:
- 클릭율 5% = 50클릭
- 구매 전환율 10% = 5건
- 평균 구매액 200,000원
- 평균 수수료 3%

월 수익: 200,000 × 5 × 0.03 = 30,000원
```

---

## 🆘 자주 묻는 질문

### Q: 쿠팡 승인이 거부되면?
```
1. 웹사이트 내용 보강 (서비스 설명 상세히)
2. 도메인 구매 (승인율 향상)
3. 재신청 (보통 1-2회 재시도 후 승인)
```

### Q: Secret Key를 복사 안 했어요
```
파트너스 센터 → 도구 → API 설정
→ "Secret Key 재발급" 클릭
(기존 키는 무효화됨)
```

### Q: 수수료가 0원이에요
```
- 딥링크 사용 확인
- 쿠키 활성화 상태에서 클릭 → 구매 완료 필요
- 정산은 주문 확정 후 (보통 구매 후 7-14일)
```

---

## 🎉 축하합니다!

네이버 + 쿠팡 API로 **수만 개의 실제 이월상품 데이터**를 확보하고,
**제휴 수수료 수익**까지 창출할 수 있습니다!

다음 단계: 클라우드 배포 및 본격 서비스 시작 🚀
