# E-wall Django API 문서

## 개요

E-wall의 RESTful API는 상품 검색, 가격 알림 설정, 클릭 트래킹 등의 기능을 제공합니다.

## 기본 정보

- **Base URL**: `http://localhost:8000/api/`
- **인증**: 현재 인증 불필요 (추후 토큰 인증 추가 예정)
- **응답 형식**: JSON

---

## 상품 API

### 1. 상품 목록 조회

브랜드와 카테고리별 상품 목록을 조회합니다.

**Endpoint**
```
GET /api/products/{brand_slug}/{category_slug}/
```

**Parameters**

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `downRatio` | string | 다운 비율 | `90-10`, `80-20` |
| `fillPowerMin` | integer | 최소 필파워 | `750` |
| `priceMax` | integer | 최대 가격 | `100000` |
| `discountMin` | integer | 최소 할인율 | `30` |
| `hood` | boolean | 후드 유무 | `true`, `false` |
| `fit` | string | 핏 | `slim`, `regular` |
| `sort` | string | 정렬 | `discount`, `price-low`, `price-high`, `newest` |
| `page` | integer | 페이지 번호 | `1` |
| `page_size` | integer | 페이지 크기 | `20` |

**예시 요청**
```http
GET /api/products/northface/down/?downRatio=90-10&fillPowerMin=750&sort=discount&page=1
```

**응답**
```json
{
  "products": [
    {
      "id": "coupang-12345",
      "brand_name": "노스페이스",
      "category_name": "다운",
      "title": "노스페이스 다운 재킷 800FP 90/10",
      "slug": "northface-down-jacket-800fp",
      "image_url": "https://example.com/image.jpg",
      "price": "89000",
      "original_price": "129000",
      "discount_rate": "31.01",
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

---

## 알림 API

### 2. 가격 알림 생성

사용자가 설정한 조건에 맞는 상품이 나타나면 이메일로 알림을 받습니다.

**Endpoint**
```
POST /api/alerts/
```

**요청 본문**
```json
{
  "email": "user@example.com",
  "brand_slug": "northface",
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

**응답**
```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000",
  "email": "user@example.com",
  "brand": "노스페이스",
  "category": "다운",
  "conditions": {
    "priceBelow": 100000,
    "discountAtLeast": 30,
    "downRatio": "90-10",
    "fillPowerMin": 750,
    "hood": false
  },
  "active": true,
  "created_at": "2025-11-21T10:00:00Z"
}
```

### 3. 알림 목록 조회

**Endpoint**
```
GET /api/alerts/list/?email={email}
```

**응답**
```json
{
  "alerts": [
    {
      "id": "123e4567-e89b-12d3-a456-426614174000",
      "email": "user@example.com",
      "brand": "노스페이스",
      "category": "다운",
      "conditions": {...},
      "active": true,
      "created_at": "2025-11-21T10:00:00Z"
    }
  ],
  "total": 1
}
```

### 4. 알림 수정

**Endpoint**
```
PUT /api/alerts/{alert_id}/
```

**요청 본문**
```json
{
  "active": false,
  "conditions": {
    "priceBelow": 80000
  }
}
```

### 5. 알림 삭제

**Endpoint**
```
DELETE /api/alerts/{alert_id}/
```

**응답**: `204 No Content`

---

## 클릭 트래킹 API

### 6. 제휴 링크 리다이렉트

상품 클릭을 추적하고 제휴 링크로 리다이렉트합니다.

**Endpoint**
```
GET /api/out/?productId={id}&subId={tracking_id}
```

**Parameters**

| 파라미터 | 타입 | 필수 | 설명 |
|---------|------|-----|------|
| `productId` | string | O | 상품 ID |
| `subId` | string | X | 추적용 ID (브랜드-카테고리 등) |

**예시 요청**
```http
GET /api/out/?productId=coupang-12345&subId=ewall-northface-down
```

**응답**: `302 Redirect` → 제휴사 딥링크

---

## 오류 응답

**400 Bad Request**
```json
{
  "error": "Invalid parameters",
  "details": {
    "email": ["This field is required"]
  }
}
```

**404 Not Found**
```json
{
  "error": "Product not found"
}
```

**500 Internal Server Error**
```json
{
  "error": "Internal server error",
  "message": "An unexpected error occurred"
}
```

---

## 조건(Conditions) 필드 스키마

알림 생성 시 사용할 수 있는 조건들입니다.

### 공통 조건

```json
{
  "priceBelow": 100000,        // 최대 가격
  "discountAtLeast": 30,       // 최소 할인율 (%)
  "fit": "slim",               // 핏
  "shell": "nylon"             // 소재
}
```

### 다운 제품 전용

```json
{
  "downType": "goose",         // 다운 타입: goose, duck, synthetic
  "downRatio": "90-10",        // 다운 비율: 90-10, 80-20, 70-30
  "fillPowerMin": 750,         // 최소 필파워
  "hood": false                // 후드 유무
}
```

### 슬랙스 전용

```json
{
  "waistType": "high",         // 허리: high, mid, low
  "legOpening": "tapered",     // 밑단: tapered, straight, wide
  "stretch": true              // 신축성 여부
}
```

### 청바지 전용

```json
{
  "wash": "dark",              // 워싱: light, medium, dark, black
  "cut": "slim",               // 컷: skinny, slim, straight, bootcut, wide
  "rise": "mid",               // 라이즈: low, mid, high
  "distressed": false          // 디스트레스 여부
}
```

---

## 사용 예시

### Python (requests)

```python
import requests

# 상품 검색
response = requests.get(
    'http://localhost:8000/api/products/northface/down/',
    params={
        'downRatio': '90-10',
        'fillPowerMin': 750,
        'sort': 'discount'
    }
)
products = response.json()

# 알림 생성
response = requests.post(
    'http://localhost:8000/api/alerts/',
    json={
        'email': 'user@example.com',
        'brand_slug': 'northface',
        'category_slug': 'down',
        'conditions': {
            'priceBelow': 100000,
            'discountAtLeast': 30,
            'downRatio': '90-10'
        }
    }
)
alert = response.json()
```

### JavaScript (fetch)

```javascript
// 상품 검색
const response = await fetch(
  'http://localhost:8000/api/products/northface/down/?downRatio=90-10&sort=discount'
);
const data = await response.json();

// 알림 생성
const alertResponse = await fetch('http://localhost:8000/api/alerts/', {
  method: 'POST',
  headers: {
    'Content-Type': 'application/json',
  },
  body: JSON.stringify({
    email: 'user@example.com',
    brand_slug: 'northface',
    category_slug: 'down',
    conditions: {
      priceBelow: 100000,
      discountAtLeast: 30,
      downRatio: '90-10'
    }
  })
});
const alert = await alertResponse.json();
```

---

## 캐싱

- 상품 목록 API는 5분간 Redis에 캐싱됩니다.
- 캐시 키: `products:{brand_slug}:{category_slug}:{query_params}`

## Rate Limiting

- 익명 사용자: 100 요청/시간
- 인증 사용자: 1000 요청/시간

---

**추가 문의사항은 GitHub Issues를 이용해주세요!**
