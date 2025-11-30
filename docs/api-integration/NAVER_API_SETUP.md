# 네이버 쇼핑 API 설정 가이드

## 1단계: API 키 발급 (5분)

### 1. 네이버 개발자센터 접속
```
https://developers.naver.com
```

### 2. 로그인 후 "Application" → "애플리케이션 등록" 클릭

### 3. 애플리케이션 정보 입력
```
애플리케이션 이름: E-wall 이월상품 검색
사용 API: [검색] 체크
비로그인 오픈 API 서비스 환경:
  - WEB 설정: http://localhost:8000
```

### 4. 등록 완료 후 발급된 정보 확인
```
Client ID: (복사) ipNNG8WSO5GKTjCY7I9M
Client Secret: (복사) dh7mixU3MN
```

---

## 2단계: 환경변수 설정

발급받은 Client ID와 Secret을 아래 파일에 추가하세요:

### `.env.development` 파일에 추가
```env
# Naver Shopping API
NAVER_CLIENT_ID=발급받은_Client_ID_여기에_붙여넣기
NAVER_CLIENT_SECRET=발급받은_Client_Secret_여기에_붙여넣기
```

### `.env.production` 파일에도 동일하게 추가
```env
# Naver Shopping API  
NAVER_CLIENT_ID=발급받은_Client_ID_여기에_붙여넣기
NAVER_CLIENT_SECRET=발급받은_Client_Secret_여기에_붙여넣기
```

---

## 3단계: 테스트 실행

```powershell
# Django shell 실행
python manage.py shell
```

```python
# 네이버 쇼핑 API 테스트
from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler

crawler = NaverShoppingCrawler()

# 단순 검색 테스트
products = crawler.search('노스페이스 다운', limit=10)
print(f"검색 결과: {len(products)}개")

# 결과 확인
for p in products[:3]:
    print(f"{p['title'][:50]} - {p['price']:,}원")

# 이월상품 검색 테스트
outlet_products = crawler.search_outlet_products(
    brands=['노스페이스', '파타고니아'],
    limit_per_brand=20
)
print(f"\n이월상품: {len(outlet_products)}개")
```

**예상 결과:**
```
검색 결과: 10개
노스페이스 NEW 눕시 다운 자켓 - 198,000원
파타고니아 다운 스웨터 후디 - 265,000원
...

이월상품: 156개
```

---

## 4단계: 실제 데이터베이스에 저장

```python
# Django shell에서 계속
from apps.products.tasks import crawl_multi_platform

# 네이버 API로 실제 상품 크롤링
result = crawl_multi_platform.apply(
    kwargs={
        'keywords': [
            '노스페이스 이월',
            '파타고니아 아울렛',
            '아크테릭스 세일',
            '밀레 이월상품'
        ],
        'platforms': ['naver']
    }
)

print(f"생성: {result['created']}개")
print(f"업데이트: {result['updated']}개")
print(f"에러: {result['errors']}개")
```

---

## 5단계: 관리자 페이지 확인

```powershell
# 개발 서버 실행
python manage.py runserver
```

브라우저에서:
```
http://localhost:8000/admin/products/genericproduct/
```

→ 실제 이월상품들이 저장되어 있습니다! 🎉

---

## ✅ 체크리스트

- [ ] 네이버 개발자센터 가입
- [ ] 애플리케이션 등록
- [ ] Client ID/Secret 발급
- [ ] .env.development 파일에 추가
- [ ] .env.production 파일에 추가
- [ ] Django shell에서 테스트
- [ ] 검색 결과 10개 이상 확인
- [ ] DB에 상품 저장 확인
- [ ] 관리자 페이지에서 상품 확인

---

## 🆘 문제 해결

### "Client ID/Secret이 유효하지 않습니다"
```
1. .env 파일 재확인 (따옴표 없이 입력)
2. 개발자센터에서 발급된 키 재확인
3. 서버 재시작 (Ctrl+C 후 다시 runserver)
```

### "상품이 0개 검색됨"
```python
# 크롤러 설정 확인
crawler = NaverShoppingCrawler()
print(f"Client ID 설정: {bool(crawler.client_id)}")
print(f"Client Secret 설정: {bool(crawler.client_secret)}")
```

### "API 호출 제한 초과"
```
네이버 무료 할당량: 일 25,000건
→ 내일 다시 시도하거나 키워드 수 줄이기
```

---

## 다음 단계: 쿠팡 파트너스

네이버 API가 정상 작동하면, 쿠팡 파트너스 신청을 진행하세요.
(별도 가이드 참조: COUPANG_PARTNERS_GUIDE.md)
