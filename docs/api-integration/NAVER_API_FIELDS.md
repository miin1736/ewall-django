# 네이버 쇼핑 검색 API 제공 정보

## 📊 API 응답 구조

네이버 쇼핑 검색 API는 다음과 같은 정보를 제공합니다:

---

## 1️⃣ 전체 응답 구조

```json
{
  "lastBuildDate": "Wed, 27 Nov 2024 12:00:00 +0900",
  "total": 12345,        // 전체 검색 결과 수
  "start": 1,            // 검색 시작 위치
  "display": 10,         // 한 번에 표시할 검색 결과 개수
  "items": [...]         // 상품 목록 배열
}
```

---

## 2️⃣ 개별 상품 정보 (items 배열)

### ✅ 제공되는 필드 (14개)

| 필드 | 설명 | 예시 | 비고 |
|------|------|------|------|
| **title** | 상품명 | `"<b>노스페이스</b> NEW 눕시 다운"` | HTML 태그 포함 |
| **link** | 구매 링크 | `"https://shopping.naver.com/..."` | **실제 구매 페이지** |
| **image** | 이미지 URL | `"https://shopping-phinf.pstatic.net/..."` | 썸네일 이미지 |
| **lprice** | 최저가 | `"198000"` | 문자열 (원) |
| **hprice** | 최고가 | `"330000"` | 원가 (할인 전), 선택적 |
| **mallName** | 쇼핑몰명 | `"쿠팡"` | 판매처 |
| **productId** | 상품 ID | `"12345678"` | 고유 식별자 |
| **productType** | 상품 유형 | `"1"` | 1:일반, 2:중고, 3:단종, 4:판매예정 |
| **brand** | 브랜드 | `"노스페이스"` | 선택적 (없을 수 있음) |
| **maker** | 제조사 | `"THE NORTH FACE"` | 선택적 |
| **category1** | 대분류 | `"패션의류"` | 선택적 |
| **category2** | 중분류 | `"남성의류"` | 선택적 |
| **category3** | 소분류 | `"아우터"` | 선택적 |
| **category4** | 세분류 | `"다운점퍼"` | 선택적 |

---

## 3️⃣ 실제 응답 예시

```json
{
  "lastBuildDate": "Wed, 27 Nov 2024 12:00:00 +0900",
  "total": 1523,
  "start": 1,
  "display": 3,
  "items": [
    {
      "title": "<b>노스페이스</b> NEW 눕시 다운 자켓 NJ1DM50",
      "link": "https://shopping.naver.com/gate.nhn?id=12345678",
      "image": "https://shopping-phinf.pstatic.net/main_1234567/12345678.jpg",
      "lprice": "198000",
      "hprice": "330000",
      "mallName": "쿠팡",
      "productId": "12345678",
      "productType": "1",
      "brand": "노스페이스",
      "maker": "THE NORTH FACE",
      "category1": "패션의류",
      "category2": "남성의류",
      "category3": "아우터",
      "category4": "다운점퍼"
    },
    {
      "title": "<b>노스페이스</b> 눕시 숏 다운 자켓",
      "link": "https://shopping.naver.com/gate.nhn?id=87654321",
      "image": "https://shopping-phinf.pstatic.net/main_8765432/87654321.jpg",
      "lprice": "165000",
      "hprice": "299000",
      "mallName": "11번가",
      "productId": "87654321",
      "productType": "1",
      "brand": "노스페이스",
      "maker": "THE NORTH FACE",
      "category1": "패션의류",
      "category2": "남성의류",
      "category3": "아우터",
      "category4": "다운점퍼"
    }
  ]
}
```

---

## 4️⃣ E-wall에서 활용하는 정보

### ✅ 핵심 필드 매핑

| 네이버 API 필드 | E-wall 모델 필드 | 용도 |
|----------------|------------------|------|
| `title` | `title` | 상품명 (HTML 태그 제거) |
| `link` | `deeplink` | **구매 링크** (클릭 시 이동) |
| `image` | `image_url` | 상품 이미지 |
| `lprice` | `price` | 현재 판매가 |
| `hprice` | `original_price` | 정가 (할인 전) |
| `mallName` | `seller` | 판매 쇼핑몰 |
| `productId` | `id` (일부) | `naver-{productId}` 형식 |
| `brand` | `brand` | 브랜드 정보 |
| `category1-4` | `category` | 카테고리 매핑 |

### 🧮 계산되는 정보

```python
# 할인율 계산
discount_rate = ((hprice - lprice) / hprice) * 100

# 예시:
# hprice: 330,000원
# lprice: 198,000원
# 할인율: ((330,000 - 198,000) / 330,000) * 100 = 40%
```

---

## 5️⃣ 중요 특징

### ✅ 제공되는 것

1. **실시간 가격** - API 호출 시점의 최신 가격
2. **실제 구매 링크** - `link` 필드로 바로 구매 가능
3. **여러 쇼핑몰 통합** - 쿠팡, 11번가, 지마켓, 옥션 등
4. **최저가 정보** - 여러 쇼핑몰 중 최저가
5. **카테고리 정보** - 4단계 카테고리 분류
6. **브랜드 정보** - 대부분의 상품에 브랜드 포함

### ⚠️ 제공되지 않는 것

1. **정확한 재고 수량** - 재고 유무만 확인 (품절은 검색 결과에서 제외)
2. **상품 옵션** - 색상, 사이즈 등 세부 옵션
3. **리뷰 수/평점** - 별도 API 없음
4. **배송비** - 쇼핑몰마다 다름
5. **상세 설명** - 상품 상세 페이지는 링크로 이동 필요

---

## 6️⃣ API 제한사항

| 항목 | 제한 |
|------|------|
| **일일 호출 횟수** | 25,000건 (무료) |
| **최대 검색 결과** | 100개/요청 |
| **응답 속도** | 평균 0.5-1초 |
| **검색 정렬** | sim(유사도), date(날짜), asc(가격↑), dsc(가격↓) |

---

## 7️⃣ E-wall 활용 예시

### 상품 카드 표시

```html
<div class="product-card">
    <img src="{{ product.image_url }}" />
    <h3>{{ product.title }}</h3>
    
    <!-- 가격 정보 -->
    <p class="original-price">{{ product.original_price|intcomma }}원</p>
    <p class="sale-price">{{ product.price|intcomma }}원</p>
    <span class="discount">{{ product.discount_rate }}% OFF</span>
    
    <!-- 판매처 -->
    <p class="seller">{{ product.seller }}</p>
    
    <!-- 구매 링크 -->
    <a href="{{ product.deeplink }}" target="_blank">
        구매하기 →
    </a>
</div>
```

### 이월상품 필터링

```python
# 할인율 30% 이상
outlet_products = GenericProduct.objects.filter(
    source='naver',
    discount_rate__gte=30,
    in_stock=True
)

# 브랜드별
northface_outlets = outlet_products.filter(
    brand__name__icontains='노스페이스'
)

# 가격대별
affordable = outlet_products.filter(
    price__lte=200000  # 20만원 이하
)
```

---

## 8️⃣ 데이터 품질 관리

### HTML 태그 제거

```python
# title 필드에 HTML 태그 포함
# 원본: "<b>노스페이스</b> NEW 눕시 다운"
# 정제 후: "노스페이스 NEW 눕시 다운"

import re
clean_title = re.sub(r'<[^>]+>', '', title)
```

### 브랜드 추출 (없는 경우)

```python
# brand 필드가 없으면 제목에서 추출
if not item.get('brand'):
    # 주요 브랜드 리스트와 매칭
    brands = ['노스페이스', '파타고니아', '아크테릭스']
    for brand in brands:
        if brand in title:
            item['brand'] = brand
            break
```

### 카테고리 매핑

```python
# 네이버 카테고리 → E-wall 카테고리
category_map = {
    '다운점퍼': 'down',
    '청바지': 'jeans',
    '슬랙스': 'slacks',
    '맨투맨': 'crewneck',
}
```

---

## 9️⃣ 실제 테스트

### 테스트 스크립트 실행 (Django 설치 필요)

```powershell
# 환경 설정 후
python scripts/check_naver_api_response.py
```

**예상 출력:**
```
================================================================================
네이버 쇼핑 검색 API 테스트
================================================================================

검색어: 노스페이스 다운
요청 중...

✅ API 호출 성공!

--------------------------------------------------------------------------------
전체 응답 구조:
--------------------------------------------------------------------------------
total: 1523개 (전체 검색 결과 수)
start: 1 (검색 시작 위치)
display: 3 (한 번에 표시할 검색 결과 개수)
items: 3개 (실제 반환된 상품 수)

================================================================================
개별 상품 정보 (items 배열 내부)
================================================================================

📦 상품 #1
--------------------------------------------------------------------------------
title           : 상품명 (HTML 태그 포함)
                  → <b>노스페이스</b> NEW 눕시 다운 자켓
link            : 상품 URL (구매 링크)
                  → https://shopping.naver.com/gate.nhn?id=12345678
lprice          : 최저가 (네이버 기준)
                  → 198,000원
hprice          : 최고가 (원가)
                  → 330,000원
할인율          : 40% OFF
mallName        : 쇼핑몰 이름
                  → 쿠팡
brand           : 브랜드
                  → 노스페이스
category1       : 대분류 카테고리
                  → 패션의류
category4       : 세분류 카테고리
                  → 다운점퍼
```

---

## 🎯 결론

네이버 쇼핑 검색 API는 **E-wall에 필요한 모든 핵심 정보**를 제공합니다:

✅ **가격 정보** (최저가, 원가, 할인율)  
✅ **구매 링크** (실제 구매 가능)  
✅ **이미지** (상품 썸네일)  
✅ **브랜드/카테고리** (필터링 가능)  
✅ **판매처** (쿠팡, 11번가 등)  
✅ **실시간 업데이트** (API 호출 시 최신 정보)

**이월상품 서비스에 완벽하게 적합합니다!** 🎉
