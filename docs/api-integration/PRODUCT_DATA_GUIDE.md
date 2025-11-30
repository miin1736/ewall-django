# 🎯 E-wall 실제 상품 데이터 확보 가이드

## 현실적인 데이터 수집 방법 (합법적 & 실용적)

---

## 1️⃣ 제휴 마케팅 API (가장 추천) ⭐⭐⭐⭐⭐

### A. 쿠팡 파트너스 (Coupang Partners)
**난이도**: ⭐☆☆☆☆  
**승인 시간**: 1-3일  
**수수료**: 1.5% - 9%  
**데이터 품질**: ⭐⭐⭐⭐⭐

#### 신청 방법
```
1. https://partners.coupang.com 회원가입
2. 웹사이트 정보 입력 (도메인, 설명)
3. 승인 대기 (보통 1-3일)
4. API 키 발급
```

#### 장점
- ✅ **무료 사용**
- ✅ **실시간 가격/재고 업데이트**
- ✅ **이월상품 카테고리 별도 제공**
- ✅ **딥링크 자동 생성** (수수료 자동 추적)
- ✅ **법적 문제 없음**
- ✅ **API 문서 한글 제공**

#### 단점
- ⚠️ 승인 필요 (블로그나 웹사이트 필요)
- ⚠️ 월 0원 수익 시 계정 정지 가능

#### 구현 예시
```python
# 쿠팡 파트너스 검색 API
import requests
import hmac
import hashlib
from datetime import datetime

def search_coupang_products(keyword, limit=100):
    ACCESS_KEY = "your-access-key"
    SECRET_KEY = "your-secret-key"
    
    url = "https://api-gateway.coupang.com/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
    
    request_method = "GET"
    datetime_str = datetime.utcnow().strftime('%y%m%d')+'T'+datetime.utcnow().strftime('%H%M%S')+'Z'
    
    # HMAC 서명 생성
    message = datetime_str + request_method + url[url.find("/v2"):]
    signature = hmac.new(
        SECRET_KEY.encode('utf-8'),
        message.encode('utf-8'),
        hashlib.sha256
    ).hexdigest()
    
    headers = {
        'Authorization': f'CEA algorithm=HmacSHA256, access-key={ACCESS_KEY}, signed-date={datetime_str}, signature={signature}',
        'Content-Type': 'application/json'
    }
    
    params = {
        'keyword': keyword,
        'limit': limit
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

# 사용 예시
products = search_coupang_products('노스페이스 다운', limit=100)
```

---

### B. 네이버 쇼핑 검색 API
**난이도**: ⭐☆☆☆☆  
**승인 시간**: 즉시  
**비용**: 무료 (일 25,000건)  
**데이터 품질**: ⭐⭐⭐⭐

#### 신청 방법
```
1. https://developers.naver.com 가입
2. 애플리케이션 등록
3. 클라이언트 ID/Secret 발급 (즉시)
```

#### 장점
- ✅ **즉시 사용 가능** (승인 불필요)
- ✅ **무료**
- ✅ **여러 쇼핑몰 통합 검색**
- ✅ **최저가 정보 제공**

#### 단점
- ⚠️ 직접 구매링크 (수수료 없음)
- ⚠️ 일 25,000건 제한

#### 구현 예시
```python
def search_naver_shopping(keyword, display=100):
    CLIENT_ID = "your-client-id"
    CLIENT_SECRET = "your-client-secret"
    
    url = "https://openapi.naver.com/v1/search/shop.json"
    
    headers = {
        'X-Naver-Client-Id': CLIENT_ID,
        'X-Naver-Client-Secret': CLIENT_SECRET
    }
    
    params = {
        'query': keyword,
        'display': display,  # 최대 100개
        'sort': 'sim'  # sim(유사도), date(날짜), asc/dsc(가격)
    }
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()
```

---

### C. 11번가 Open API
**난이도**: ⭐⭐☆☆☆  
**승인 시간**: 1-2주  
**수수료**: 2% - 6%  
**데이터 품질**: ⭐⭐⭐⭐

#### 신청 방법
```
1. https://openapi.11st.co.kr 가입
2. API 신청 (사업 목적 설명 필요)
3. 승인 대기
```

---

### D. 링크프라이스 (다중 쇼핑몰 통합)
**난이도**: ⭐⭐⭐☆☆  
**승인 시간**: 1주  
**수수료**: 쇼핑몰별 상이  
**데이터 품질**: ⭐⭐⭐⭐

#### 특징
- 여러 쇼핑몰 한번에 연동 (G마켓, 옥션, 11번가, 위메프 등)
- 수수료 정산 자동화

---

## 2️⃣ 공식 오픈마켓 셀러 API (진지한 비즈니스)

### 네이버 스마트스토어 API
```
- 본인이 스마트스토어 판매자로 등록
- 타 셀러 상품 데이터 가져오기 (제휴)
- 셀러 API로 상품 정보 크롤링
```

**장점**: 완전한 데이터 제어  
**단점**: 초기 설정 복잡

---

## 3️⃣ RSS 피드 수집 (무료, 제한적)

### 주요 쇼핑몰 RSS
```xml
<!-- 쿠팡 로켓배송 -->
https://www.coupang.com/np/categories/[category-id]/rss

<!-- G마켓 베스트 -->
http://item.gmarket.co.kr/Bestsellers/RSS/BestSeller_Item.asp

<!-- 옥션 -->
http://browse.auction.co.kr/rss/best_rss.xml
```

**장점**: 무료, 승인 불필요  
**단점**: 데이터 제한적, 이월상품 특화 아님

---

## 4️⃣ 웹 스크래핑 (비추천, 법적 리스크)

### ⚠️ 주의사항
```
- robots.txt 확인 필수
- 크롤링 금지된 사이트 다수
- IP 차단 위험
- 법적 분쟁 가능성
- 데이터 변경 시 코드 깨짐
```

**결론**: 개인 프로젝트 외에는 피해야 함

---

## 🎯 E-wall 맞춤 추천 전략

### Phase 1: 즉시 시작 (오늘부터 가능)
```python
✅ 네이버 쇼핑 검색 API
   - 즉시 사용 가능
   - 무료 25,000건/일
   - 이월상품 키워드 검색
   
구현:
1. 네이버 개발자센터 가입
2. 앱 등록 (5분)
3. 코드 수정 (아래 제공)
4. 배포!
```

### Phase 2: 1주일 이내
```python
✅ 쿠팡 파트너스 승인 대기
   - 웹사이트/블로그 제출
   - 1-3일 승인
   - 실시간 가격 데이터
   
준비물:
- 도메인 (무료 가능)
- 간단한 소개 페이지
```

### Phase 3: 수익화 단계
```python
✅ 링크프라이스 연동
   - 다중 쇼핑몰 통합
   - 수수료 정산 자동화
```

---

## 💻 실제 구현 코드 (즉시 적용 가능)

### 1. 네이버 쇼핑 API 크롤러 추가
```python
# apps/products/services/crawlers/naver_crawler.py
import requests
from typing import List, Dict
from django.conf import settings

class NaverShoppingCrawler:
    def __init__(self):
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        self.base_url = "https://openapi.naver.com/v1/search/shop.json"
    
    def search(self, keyword: str, limit: int = 100) -> List[Dict]:
        """네이버 쇼핑 검색"""
        headers = {
            'X-Naver-Client-Id': self.client_id,
            'X-Naver-Client-Secret': self.client_secret
        }
        
        params = {
            'query': keyword,
            'display': min(limit, 100),
            'sort': 'sim'
        }
        
        response = requests.get(self.base_url, headers=headers, params=params)
        response.raise_for_status()
        
        data = response.json()
        return self._normalize(data.get('items', []))
    
    def _normalize(self, items: List[Dict]) -> List[Dict]:
        """데이터 정규화"""
        normalized = []
        
        for item in items:
            # HTML 태그 제거
            title = item['title'].replace('<b>', '').replace('</b>', '')
            
            normalized.append({
                'platform': 'naver',
                'product_id': item['productId'],
                'title': title,
                'brand': item.get('brand', ''),
                'price': int(item['lprice']),
                'original_price': int(item.get('hprice', item['lprice'])),
                'image_url': item['image'],
                'product_url': item['link'],
                'category': item.get('category1', '기타'),
                'mall_name': item.get('mallName', ''),
                'in_stock': True,
            })
        
        return normalized
```

### 2. 이월상품 특화 키워드
```python
# config/keywords.py
OUTLET_KEYWORDS = [
    # 브랜드 + 이월/할인 키워드 조합
    "노스페이스 이월",
    "파타고니아 세일",
    "아크테릭스 아울렛",
    "밀레 이월",
    "코오롱스포츠 할인",
    "네파 이월상품",
    "블랙야크 아울렛",
    
    # 카테고리 + 이월
    "다운점퍼 이월",
    "패딩 이월상품",
    "등산복 아울렛",
    "아웃도어 세일",
    
    # 시즌 특화
    "겨울옷 이월",
    "작년 다운",
    "재고처리 패딩",
]

# 브랜드별 이월상품 페이지 직접 수집 (수동 큐레이션)
BRAND_OUTLET_URLS = {
    '노스페이스': 'https://www.thenorthfacekorea.co.kr/display/category?ctgrNo=1000000438',
    '밀레': 'https://www.millet.co.kr/display/category?ctgrNo=1000000123',
    # 각 브랜드 공식몰의 이월상품 카테고리
}
```

---

## 🔥 즉시 적용 가능한 솔루션

### 옵션 1: 네이버 쇼핑 API만 사용 (가장 빠름)
```
시간: 1시간
비용: 무료
상품 수: 수천 개

장점:
✅ 오늘 바로 시작
✅ 승인 불필요
✅ 법적 문제 없음
✅ 여러 쇼핑몰 통합 검색
```

### 옵션 2: 네이버 + 쿠팡 파트너스 (추천)
```
시간: 3-5일 (쿠팡 승인 대기)
비용: 무료
상품 수: 수만 개

장점:
✅ 실시간 가격 업데이트
✅ 수수료 수익 가능
✅ 이월상품 전문 카테고리
✅ 딥링크 자동 생성
```

### 옵션 3: Full 제휴 마케팅 (수익화)
```
시간: 2-4주
비용: 무료
상품 수: 수십만 개

구성:
✅ 쿠팡 파트너스
✅ 네이버 쇼핑 API
✅ 링크프라이스 (G마켓, 11번가, 위메프)
✅ 11번가 Open API

예상 수익: 월 100만원+ (트래픽 1만명 기준)
```

---

## 📋 실행 체크리스트

### 1단계: 네이버 API (오늘)
- [ ] 네이버 개발자센터 가입
- [ ] 애플리케이션 등록
- [ ] Client ID/Secret 발급
- [ ] .env 파일에 추가
- [ ] NaverShoppingCrawler 생성
- [ ] 테스트 실행

### 2단계: 쿠팡 파트너스 (3일)
- [ ] 쿠팡 파트너스 가입
- [ ] 웹사이트 정보 입력
- [ ] 승인 대기
- [ ] API 키 발급
- [ ] CoupangCrawler 업데이트
- [ ] 딥링크 생성 로직 추가

### 3단계: 데이터 수집 자동화
- [ ] Celery 태스크 수정
- [ ] 이월상품 키워드 설정
- [ ] 크롤링 스케줄 조정 (4시간 → 1시간)
- [ ] 가격 모니터링 강화

---

## 💡 Pro Tips

### 1. 이월상품 필터링
```python
def is_outlet_product(title: str, discount_rate: int) -> bool:
    """이월상품 판별"""
    outlet_keywords = ['이월', '아울렛', 'outlet', '재고', '세일', 'SALE']
    
    # 제목에 이월 키워드 포함
    has_keyword = any(kw in title.lower() for kw in outlet_keywords)
    
    # 할인율 30% 이상
    high_discount = discount_rate >= 30
    
    return has_keyword or high_discount
```

### 2. 브랜드 화이트리스트
```python
PREMIUM_BRANDS = [
    '노스페이스', '파타고니아', '아크테릭스', '밀레', '마무트',
    '코오롱스포츠', '네파', '블랙야크', '아이더', '케이투',
    '살로몬', '호그롤프스', '잭울프스킨', '컬럼비아'
]
```

### 3. 데이터 품질 관리
```python
# 중복 제거
# 같은 상품이 여러 쇼핑몰에 있을 수 있음
# 제목 + 브랜드로 유사도 검사

from difflib import SequenceMatcher

def is_duplicate(title1: str, title2: str, threshold=0.85) -> bool:
    ratio = SequenceMatcher(None, title1, title2).ratio()
    return ratio >= threshold
```

---

## 🚀 최종 추천

### 지금 당장 시작: 네이버 쇼핑 API
1. 5분 만에 API 키 발급
2. 제공된 코드 복사
3. 키워드 리스트 입력
4. 크롤링 시작

### 1주일 내: 쿠팡 파트너스 추가
1. 간단한 소개 페이지 제작 (Notion도 가능)
2. 쿠팡 파트너스 신청
3. 승인 후 API 연동
4. 수익화 시작

### 장기 전략: 다중 제휴사 통합
- 여러 API 병렬 수집
- 가격 비교 기능 강화
- 수수료 수익 극대화

**결론**: 크롤링보다 제휴 마케팅 API가 **더 쉽고, 합법적이며, 수익까지 가능**합니다! 🎉
