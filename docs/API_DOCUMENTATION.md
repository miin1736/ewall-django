# E-wall API 문서

**E-wall Django REST API v1.0**

이 문서는 E-wall 플랫폼의 RESTful API 전체 엔드포인트를 설명합니다.

## 📚 대화형 API 문서

프로젝트는 Swagger/OpenAPI 3.0 기반의 대화형 API 문서를 제공합니다:

- **Swagger UI**: http://localhost:8000/api/schema/swagger-ui/
- **ReDoc**: http://localhost:8000/api/schema/redoc/
- **OpenAPI Schema**: http://localhost:8000/api/schema/

## 기본 정보

**Base URL**: `http://localhost:8000/api/`

**Content-Type**: `application/json`

**인증**: 현재 인증 불필요 (향후 Token 인증 추가 예정)

---

## 📦 상품 (Products)

### 1. 상품 목록 조회

**카테고리별 상품 목록**

```http
GET /api/products/{category_slug}/
```

**Path Parameters:**
- `category_slug` (string, required): 카테고리 슬러그
  - 가능한 값: `down`, `coat`, `jeans`, `slacks`, `crewneck`, `long-sleeve`, `generic`

**Query Parameters:**

| 파라미터 | 타입 | 설명 | 예시 |
|---------|------|------|------|
| `search` | string | 상품명 검색 | `노스페이스` |
| `brand` | string | 브랜드 슬러그 | `the-north-face` |
| `price_min` | integer | 최소 가격 | `50000` |
| `price_max` | integer | 최대 가격 | `200000` |
| `discount_min` | integer | 최소 할인율 (%) | `30` |
| `in_stock` | boolean | 재고 여부 | `true` |
| `ordering` | string | 정렬 | `-discount_rate` |
| `page` | integer | 페이지 번호 | `1` |
| `page_size` | integer | 페이지 크기 | `20` |

**정렬 옵션 (`ordering`):**
- `price`: 가격 오름차순
- `-price`: 가격 내림차순
- `discount_rate`: 할인율 오름차순
- `-discount_rate`: 할인율 내림차순
- `-created_at`: 최신순
- `title`: 이름순

**응답 예시:**

```json
{
  "count": 150,
  "next": "http://localhost:8000/api/products/down/?page=2",
  "previous": null,
  "results": [
    {
      "id": "89983022293",
      "title": "노스페이스 25년 공용 로얄톤 프로 집업 플리스 NJ4FR51J",
      "slug": "noseupeiseu-25nyeon-gongyong-royalton-peuro-jib-eob-peulliseu-nj4fr51j",
      "category": {
        "id": 11,
        "name": "긴팔",
        "slug": "long-sleeve"
      },
      "brand": {
        "id": 2,
        "name": "노스페이스",
        "slug": "the-north-face"
      },
      "image_url": "https://shopping-phinf.pstatic.net/main_8998302/89983022293.jpg",
      "price": "59900.00",
      "original_price": "119000.00",
      "discount_rate": 50,
      "currency": "KRW",
      "seller": "네이버쇼핑",
      "deeplink": "https://search.shopping.naver.com/gate.nhn?id=89983022293",
      "in_stock": true,
      "score": null,
      "source": "naver",
      "material_composition": null,
      "created_at": "2025-11-30T12:00:00Z",
      "updated_at": "2025-11-30T12:00:00Z",
      "fit": null,
      "shell": null
    }
  ]
}
```

### 2. 상품 상세 조회

```http
GET /api/products/{category_slug}/{product_id}/
```

**Path Parameters:**
- `category_slug` (string, required): 카테고리 슬러그
- `product_id` (string, required): 상품 ID

**응답 예시:**

```json
{
  "id": "89983022293",
  "title": "노스페이스 25년 공용 로얄톤 프로 집업 플리스 NJ4FR51J",
  "slug": "noseupeiseu-25nyeon-gongyong-royalton-peuro-jib-eob-peulliseu-nj4fr51j",
  "category": {
    "id": 11,
    "name": "긴팔",
    "slug": "long-sleeve",
    "description": "긴팔 상의",
    "category_type": "long_sleeve"
  },
  "brand": {
    "id": 2,
    "name": "노스페이스",
    "slug": "the-north-face",
    "description": "The North Face - 프리미엄 아웃도어 브랜드"
  },
  "image_url": "https://shopping-phinf.pstatic.net/main_8998302/89983022293.jpg",
  "price": "59900.00",
  "original_price": "119000.00",
  "discount_rate": 50,
  "currency": "KRW",
  "seller": "네이버쇼핑",
  "deeplink": "https://search.shopping.naver.com/gate.nhn?id=89983022293",
  "in_stock": true,
  "score": null,
  "source": "naver",
  "material_composition": "polyester 95%, elastane 5%",
  "created_at": "2025-11-30T12:00:00Z",
  "updated_at": "2025-11-30T12:00:00Z",
  "fit": "regular",
  "shell": null
}
```

---

## 🤖 AI 추천 (Recommendations)

### 3. 유사 상품 추천 (이미지 기반)

**ResNet50 + FAISS 벡터 검색**

```http
GET /api/recommendations/similar-images/{product_id}/
```

**Path Parameters:**
- `product_id` (string, required): 기준 상품 ID

**Query Parameters:**

| 파라미터 | 타입 | 기본값 | 설명 |
|---------|------|--------|------|
| `limit` | integer | 10 | 반환할 상품 수 (최대 50) |
| `min_similarity` | float | 0.5 | 최소 유사도 (0-1) |
| `rebuild` | boolean | false | 임베딩 재생성 여부 |

**응답 예시:**

```json
{
  "product_id": "89983022293",
  "source_product": {
    "name": "노스페이스 25년 공용 로얄톤 프로 집업 플리스",
    "image_url": "https://shopping-phinf.pstatic.net/main_8998302/89983022293.jpg",
    "category": "긴팔",
    "brand": "노스페이스"
  },
  "similar_products": [
    {
      "product_id": "89128948114",
      "name": "네파 남성 기능성 집업 티셔츠 폴라텍 플리스",
      "brand": "네파",
      "category": "긴팔",
      "category_slug": "long-sleeve",
      "image_url": "https://shopping-phinf.pstatic.net/main_8912894/89128948114.jpg",
      "price": 45900.0,
      "discount_rate": 45,
      "final_price": 25245.0,
      "similarity_score": 0.6520,
      "distance": 0.5337,
      "style_match": "매우 유사한 스타일"
    },
    {
      "product_id": "83630826564",
      "name": "네파 여성 집업 긴팔 등산 티셔츠",
      "brand": "네파",
      "category": "긴팔",
      "category_slug": "long-sleeve",
      "image_url": "https://shopping-phinf.pstatic.net/main_8363082/83630826564.jpg",
      "price": 39900.0,
      "discount_rate": 40,
      "final_price": 23940.0,
      "similarity_score": 0.6502,
      "distance": 0.5387,
      "style_match": "유사한 스타일"
    }
  ],
  "total_count": 10,
  "search_params": {
    "limit": 10,
    "min_similarity": 0.5,
    "same_category_only": true
  },
  "description": "긴팔 카테고리에서 비슷한 스타일의 상품을 추천합니다"
}
```

### 4. FAISS 인덱스 통계

```http
GET /api/recommendations/image-index-stats/
```

**응답 예시:**

```json
{
  "faiss_index": {
    "total_vectors": 422,
    "dimension": 2048,
    "index_file_exists": true
  },
  "database": {
    "total_embeddings": 422,
    "products_with_images": 388,
    "coverage_rate": 108.8
  },
  "status": "healthy"
}
```

---

## 🏷️ 브랜드 & 카테고리

### 5. 브랜드 목록

```http
GET /api/brands/
```

**응답 예시:**

```json
{
  "count": 15,
  "results": [
    {
      "id": 1,
      "name": "노스페이스",
      "slug": "the-north-face",
      "description": "The North Face - 프리미엄 아웃도어 브랜드",
      "website": "https://www.thenorthface.co.kr",
      "is_premium": true,
      "product_count": 120
    },
    {
      "id": 2,
      "name": "파타고니아",
      "slug": "patagonia",
      "description": "Patagonia - 친환경 아웃도어 브랜드",
      "website": "https://www.patagonia.co.kr",
      "is_premium": true,
      "product_count": 85
    }
  ]
}
```

### 6. 카테고리 목록

```http
GET /api/categories/
```

**응답 예시:**

```json
{
  "count": 7,
  "results": [
    {
      "id": 7,
      "name": "다운",
      "slug": "down",
      "category_type": "down",
      "description": "다운 재킷 및 패딩",
      "product_count": 52
    },
    {
      "id": 12,
      "name": "코트",
      "slug": "coat",
      "category_type": "coat",
      "description": "코트 및 자켓",
      "product_count": 75
    }
  ]
}
```

---

## 🔔 알림 (Alerts)

### 7. 가격 알림 생성

```http
POST /api/alerts/
Content-Type: application/json
```

**요청 Body:**

```json
{
  "email": "user@example.com",
  "brand_slug": "the-north-face",
  "category_slug": "down",
  "conditions": {
    "priceBelow": 150000,
    "discountAtLeast": 40
  },
  "is_active": true
}
```

**응답 예시:**

```json
{
  "id": 123,
  "email": "user@example.com",
  "brand": {
    "id": 1,
    "name": "노스페이스",
    "slug": "the-north-face"
  },
  "category": {
    "id": 7,
    "name": "다운",
    "slug": "down"
  },
  "conditions": {
    "priceBelow": 150000,
    "discountAtLeast": 40
  },
  "is_active": true,
  "created_at": "2025-11-30T12:00:00Z",
  "last_checked": null,
  "matched_count": 0
}
```

### 8. 내 알림 목록

```http
GET /api/alerts/?email=user@example.com
```

**응답 예시:**

```json
{
  "count": 3,
  "results": [
    {
      "id": 123,
      "email": "user@example.com",
      "brand": {
        "name": "노스페이스",
        "slug": "the-north-face"
      },
      "category": {
        "name": "다운",
        "slug": "down"
      },
      "conditions": {
        "priceBelow": 150000,
        "discountAtLeast": 40
      },
      "is_active": true,
      "created_at": "2025-11-30T12:00:00Z",
      "last_checked": "2025-11-30T14:00:00Z",
      "matched_count": 5
    }
  ]
}
```

### 9. 알림 삭제

```http
DELETE /api/alerts/{alert_id}/
```

**응답:**
```
204 No Content
```

---

## 📊 분석 (Analytics)

### 10. 클릭 트래킹

```http
GET /api/out/?productId={product_id}&subId={tracking_id}
```

**Query Parameters:**
- `productId` (string, required): 상품 ID
- `subId` (string, optional): 추적 ID (예: 캠페인 코드)

**동작:**
1. 클릭 이벤트 DB에 기록
2. 상품의 deeplink URL로 302 리다이렉트

**응답:**
```
302 Found
Location: https://search.shopping.naver.com/gate.nhn?id=89983022293
```

### 11. 클릭 통계

```http
GET /api/analytics/clicks/stats/
```

**Query Parameters:**

| 파라미터 | 타입 | 설명 |
|---------|------|------|
| `start_date` | date | 시작일 (YYYY-MM-DD) |
| `end_date` | date | 종료일 (YYYY-MM-DD) |
| `product_id` | string | 특정 상품 필터 |
| `brand_slug` | string | 특정 브랜드 필터 |

**응답 예시:**

```json
{
  "total_clicks": 1250,
  "unique_users": 890,
  "by_date": [
    {
      "date": "2025-11-25",
      "clicks": 120,
      "unique_users": 95
    },
    {
      "date": "2025-11-26",
      "clicks": 145,
      "unique_users": 108
    }
  ],
  "top_products": [
    {
      "product_id": "89983022293",
      "product_name": "노스페이스 25년 공용 로얄톤 프로 집업 플리스",
      "clicks": 45,
      "conversion_rate": 12.5
    }
  ],
  "top_brands": [
    {
      "brand": "노스페이스",
      "clicks": 350,
      "percentage": 28.0
    }
  ]
}
```

---

## 🔍 검색 (Search)

### 12. 통합 검색

```http
GET /api/search/?q={query}
```

**Query Parameters:**
- `q` (string, required): 검색어
- `category` (string, optional): 카테고리 필터
- `brand` (string, optional): 브랜드 필터
- `page` (integer): 페이지 번호
- `page_size` (integer): 페이지 크기

**응답 예시:**

```json
{
  "query": "플리스",
  "count": 45,
  "results": [
    {
      "id": "89983022293",
      "title": "노스페이스 25년 공용 로얄톤 프로 집업 플리스",
      "category": "긴팔",
      "brand": "노스페이스",
      "price": "59900.00",
      "discount_rate": 50,
      "image_url": "https://shopping-phinf.pstatic.net/main_8998302/89983022293.jpg",
      "relevance_score": 0.95
    }
  ]
}
```

---

## ❌ 에러 응답

### 공통 에러 형식

```json
{
  "error": "에러 메시지",
  "code": "ERROR_CODE",
  "details": {
    "field": ["상세 에러 메시지"]
  }
}
```

### HTTP 상태 코드

| 코드 | 의미 | 예시 |
|------|------|------|
| 200 | 성공 | 데이터 조회 성공 |
| 201 | 생성됨 | 알림 생성 성공 |
| 204 | 내용 없음 | 삭제 성공 |
| 400 | 잘못된 요청 | 파라미터 오류 |
| 404 | 찾을 수 없음 | 상품/리소스 없음 |
| 500 | 서버 오류 | 내부 서버 오류 |
| 503 | 서비스 불가 | AI 기능 비활성화 |

### 에러 예시

**400 Bad Request:**
```json
{
  "error": "Invalid parameter",
  "details": {
    "min_similarity": ["min_similarity must be between 0 and 1"]
  }
}
```

**404 Not Found:**
```json
{
  "error": "Product 12345 not found"
}
```

**503 Service Unavailable (AI 패키지 없음):**
```json
{
  "error": "AI 기능을 사용할 수 없습니다",
  "reason": "필수 Python 패키지가 설치되지 않았습니다",
  "missing_packages": ["torch", "torchvision", "faiss-cpu"],
  "install_command": "pip install torch torchvision faiss-cpu"
}
```

---

## 📌 API 사용 예시

### Python (requests)

```python
import requests

# 상품 목록 조회
response = requests.get(
    'http://localhost:8000/api/products/down/',
    params={
        'brand': 'the-north-face',
        'price_max': 200000,
        'discount_min': 30,
        'ordering': '-discount_rate'
    }
)
products = response.json()

# 유사 상품 추천
response = requests.get(
    'http://localhost:8000/api/recommendations/similar-images/89983022293/',
    params={
        'limit': 10,
        'min_similarity': 0.5
    }
)
similar = response.json()

# 가격 알림 생성
response = requests.post(
    'http://localhost:8000/api/alerts/',
    json={
        'email': 'user@example.com',
        'brand_slug': 'the-north-face',
        'category_slug': 'down',
        'conditions': {
            'priceBelow': 150000,
            'discountAtLeast': 40
        }
    }
)
alert = response.json()
```

### JavaScript (Fetch)

```javascript
// 상품 목록 조회
fetch('http://localhost:8000/api/products/down/?brand=the-north-face&discount_min=30')
  .then(res => res.json())
  .then(data => console.log(data.results));

// 유사 상품 추천
fetch('http://localhost:8000/api/recommendations/similar-images/89983022293/?limit=10')
  .then(res => res.json())
  .then(data => console.log(data.similar_products));

// 가격 알림 생성
fetch('http://localhost:8000/api/alerts/', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    email: 'user@example.com',
    brand_slug: 'the-north-face',
    category_slug: 'down',
    conditions: {
      priceBelow: 150000,
      discountAtLeast: 40
    }
  })
})
.then(res => res.json())
.then(data => console.log(data));
```

### cURL

```bash
# 상품 목록 조회
curl "http://localhost:8000/api/products/down/?brand=the-north-face&discount_min=30"

# 유사 상품 추천
curl "http://localhost:8000/api/recommendations/similar-images/89983022293/?limit=10"

# 가격 알림 생성
curl -X POST http://localhost:8000/api/alerts/ \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "brand_slug": "the-north-face",
    "category_slug": "down",
    "conditions": {
      "priceBelow": 150000,
      "discountAtLeast": 40
    }
  }'
```

---

## 🔄 페이지네이션

모든 목록 API는 DRF PageNumberPagination을 사용합니다.

**기본 페이지 크기**: 20개

**응답 형식:**
```json
{
  "count": 150,
  "next": "http://localhost:8000/api/products/down/?page=2",
  "previous": null,
  "results": [...]
}
```

**페이지 크기 변경:**
```http
GET /api/products/down/?page_size=50
```

---

## 📝 추가 정보

### 개발 환경 API 테스트

```bash
# 서버 실행
python manage.py runserver

# Swagger UI 접속
http://localhost:8000/api/schema/swagger-ui/
```

### 프로덕션 환경 주의사항

1. **HTTPS 사용**: 프로덕션 환경에서는 반드시 HTTPS 사용
2. **CORS 설정**: 필요한 도메인만 허용
3. **Rate Limiting**: DRF Throttling 설정 권장
4. **인증**: Token 기반 인증 추가 예정

### 관련 문서

- [아키텍처 문서](ARCHITECTURE.md)
- [기술 스택](TECH_STACK.md)
- [AI 기능 가이드](AI_STATUS_REPORT.md)
