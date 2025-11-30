# Product Filter API Documentation

## Endpoint

```
GET /api/products/{brand_slug}/{category_slug}/
```

## Description

고급 필터링을 지원하는 상품 목록 API입니다. 12개 이상의 필터 조건을 조합하여 정확한 상품을 찾을 수 있으며, 필터 메타데이터를 제공하여 동적 UI 구성이 가능합니다.

## Path Parameters

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| brand_slug | string | Yes | 브랜드 슬러그 (예: `northface`, `patagonia`) |
| category_slug | string | Yes | 카테고리 슬러그 (예: `down`, `slacks`, `jeans`) |

## Query Parameters

### 공통 필터 (모든 카테고리)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| priceMin | integer | 최소 가격 | `50000` |
| priceMax | integer | 최대 가격 | `500000` |
| discountMin | integer | 최소 할인율 (%) | `30` |
| discountMax | integer | 최대 할인율 (%) | `70` |
| fit | string | 핏 (쉼표 구분 다중 선택) | `slim,regular` |
| shell | string | 소재 (쉼표 구분 다중 선택) | `nylon,polyester` |
| inStock | boolean | 재고 여부 | `true` |
| sort | string | 정렬 방식 | `discount` (기본값) |
| page | integer | 페이지 번호 (1부터 시작) | `1` |
| page_size | integer | 페이지당 상품 수 (기본 20) | `20` |

### 정렬 옵션 (sort)

- `discount`: 할인율 높은 순 (기본값)
- `price-low`: 낮은 가격순
- `price-high`: 높은 가격순
- `newest`: 최신 등록순
- `popular`: 인기순 (클릭 수 기준)

### 다운 제품 전용 필터 (category_slug=down)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| downRatio | string | 다운 비율 | `90/10`, `80/20`, `70/30` |
| fillPowerMin | integer | 최소 필파워 | `700` |
| fillPowerMax | integer | 최대 필파워 | `900` |
| hood | boolean | 후드 여부 | `true` |
| downType | string | 다운 타입 (쉼표 구분) | `goose,duck` |

### 슬랙스 전용 필터 (category_slug=slacks)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| waistType | string | 허리 타입 | `elastic`, `button`, `drawstring` |
| legOpening | string | 밑단 타입 | `straight`, `tapered`, `wide` |
| stretch | boolean | 신축성 여부 | `true` |
| pleats | boolean | 주름 여부 | `true` |

### 청바지 전용 필터 (category_slug=jeans)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| wash | string | 워싱 (쉼표 구분) | `light,medium,dark` |
| cut | string | 컷 (쉼표 구분) | `skinny,slim,straight,relaxed,bootcut` |
| rise | string | 라이즈 | `low`, `mid`, `high` |
| distressed | boolean | 디스트레스 여부 | `true` |

### 상의 전용 필터 (category_slug=crewneck, long-sleeve)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| neckline | string | 넥라인 | `crew`, `v-neck`, `mock` |
| sleeveLength | string | 소매 길이 | `short`, `long`, `three-quarter` |
| pattern | string | 패턴 (쉼표 구분) | `solid,striped,checked` |

### 코트 전용 필터 (category_slug=coat)

| Parameter | Type | Description | Example |
|-----------|------|-------------|---------|
| length | string | 기장 | `short`, `mid`, `long` |
| closure | string | 잠금 방식 | `zipper`, `button`, `snap` |
| lining | boolean | 안감 여부 | `true` |

## Response

### Success Response (200 OK)

```json
{
  "products": [
    {
      "id": "prod_123",
      "brand_name": "노스페이스",
      "category_name": "다운",
      "title": "노스페이스 히말라야 다운 재킷",
      "slug": "northface-himalaya-down-jacket",
      "image_url": "https://example.com/images/prod_123.jpg",
      "price": 299000,
      "original_price": 599000,
      "discount_rate": 50.08,
      "in_stock": true,
      "score": 4.5,
      
      "down_type": "goose",
      "down_ratio": "90/10",
      "fill_power": 800,
      "hood": true,
      "fit": "regular",
      "shell": "nylon"
    }
  ],
  
  "total": 150,
  "page": 1,
  "page_size": 20,
  "total_pages": 8,
  "sort": "discount",
  
  "filters_applied": {
    "downRatio": "90/10",
    "fillPowerMin": "700",
    "hood": "true",
    "priceMax": "500000"
  },
  
  "available_filters": {
    "downRatio": ["90/10", "80/20", "70/30"],
    "fillPower": {
      "min": 700,
      "max": 900
    },
    "downType": ["goose", "duck"],
    "hood": true,
    "fit": ["regular", "slim", "oversized"],
    "shell": ["nylon", "polyester"]
  },
  
  "price_range": {
    "min": 50000,
    "max": 500000
  },
  
  "discount_range": {
    "min": 10,
    "max": 70
  }
}
```

### Error Responses

**404 Not Found** - 브랜드 또는 카테고리를 찾을 수 없음
```json
{
  "detail": "Not found."
}
```

**400 Bad Request** - 잘못된 쿼리 파라미터
```json
{
  "detail": "Invalid parameter: fillPowerMin must be an integer"
}
```

## Examples

### 1. 기본 상품 목록 조회

```bash
GET /api/products/northface/down/
```

### 2. 다운비율 90/10, 필파워 700 이상 필터

```bash
GET /api/products/northface/down/?downRatio=90/10&fillPowerMin=700
```

### 3. 복합 필터 (다운비율 + 필파워 + 후드 + 핏 + 가격)

```bash
GET /api/products/northface/down/?downRatio=90/10&fillPowerMin=800&hood=true&fit=slim&priceMax=300000&discountMin=50
```

### 4. 다중 값 필터 (핏 여러 개 선택)

```bash
GET /api/products/northface/down/?fit=slim,regular&shell=nylon,polyester
```

### 5. 정렬 및 페이지네이션

```bash
GET /api/products/northface/down/?sort=price-low&page=2&page_size=30
```

### 6. 슬랙스 필터 예시

```bash
GET /api/products/northface/slacks/?waistType=elastic&legOpening=tapered&stretch=true&priceMax=150000
```

## Frontend Integration Example (React)

```typescript
// API 클라이언트 함수
interface ProductFilters {
  downRatio?: string;
  fillPowerMin?: number;
  fillPowerMax?: number;
  hood?: boolean;
  fit?: string[];
  shell?: string[];
  priceMin?: number;
  priceMax?: number;
  discountMin?: number;
  sort?: 'discount' | 'price-low' | 'price-high' | 'newest' | 'popular';
  page?: number;
  page_size?: number;
}

async function fetchProducts(
  brandSlug: string,
  categorySlug: string,
  filters: ProductFilters
) {
  const params = new URLSearchParams();
  
  // 배열은 쉼표로 join
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== null) {
      if (Array.isArray(value)) {
        params.set(key, value.join(','));
      } else {
        params.set(key, String(value));
      }
    }
  });
  
  const url = `/api/products/${brandSlug}/${categorySlug}/?${params.toString()}`;
  const response = await fetch(url);
  
  if (!response.ok) {
    throw new Error('Failed to fetch products');
  }
  
  return response.json();
}

// 사용 예시
const result = await fetchProducts('northface', 'down', {
  downRatio: '90/10',
  fillPowerMin: 800,
  hood: true,
  fit: ['slim', 'regular'],
  priceMax: 500000,
  sort: 'discount',
  page: 1,
  page_size: 20
});

console.log(`Total: ${result.total} products`);
console.log(`Available filters:`, result.available_filters);
```

## Performance

- **캐싱**: 동일한 필터 조합은 5분간 Redis에 캐싱됩니다.
- **응답 시간**: 500개 상품 기준 평균 150ms 이하 (캐시 미스)
- **응답 시간**: 캐시 히트 시 10ms 이하

## Notes

1. **다중 값 필터**: `fit`, `shell`, `downType`, `wash`, `cut`, `pattern` 등은 쉼표(`,`)로 구분하여 여러 값을 선택할 수 있습니다.
2. **Boolean 파라미터**: `true` 또는 `false` 문자열로 전달합니다 (대소문자 무관).
3. **캐시 무효화**: 상품이 업데이트되면 관련 캐시가 자동으로 삭제됩니다.
4. **메타데이터 활용**: `available_filters`를 사용하여 동적으로 필터 UI를 구성할 수 있습니다.
