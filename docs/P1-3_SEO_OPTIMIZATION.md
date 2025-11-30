# P1-3: SEO 최적화 시스템

## 개요

E-wall의 검색 엔진 최적화(SEO)를 위한 포괄적인 솔루션입니다. 메타 태그 생성, Schema.org 구조화 데이터, Sitemap, Robots.txt 등을 자동화하여 검색 노출을 극대화합니다.

**구현 일자**: 2025-01-XX  
**작성자**: Development Team  
**관련 이슈**: #3 (SEO 최적화)

---

## 주요 기능

### 1. SEO 메타 태그 자동 생성
- **OG (Open Graph) 태그**: 소셜 미디어 공유 최적화
- **Twitter Card 태그**: 트위터 공유 최적화
- **Canonical URL**: 중복 콘텐츠 방지
- **동적 Meta Description**: 160자 제한, 할인율 포함
- **키워드 생성**: 브랜드/카테고리 기반 자동 생성

### 2. Schema.org 구조화 데이터
- **Product Schema**: 상품 정보, 가격, 재고, 브랜드
- **CollectionPage Schema**: 랜딩 페이지 (최대 10개 상품)
- **Breadcrumb Schema**: 네비게이션 경로
- **Organization Schema**: 회사 정보, 로고, 소셜 링크

### 3. Sitemap 최적화
- **LandingPageSitemap**: 브랜드×카테고리 조합 (daily, priority 0.8)
- **ProductDetailSitemap**: 개별 상품 (weekly, priority 0.6-0.9)
- **ProductImageSitemap**: 상품 이미지 (monthly, limit 1000)

### 4. Robots.txt 생성
- 크롤러별 규칙 (Googlebot, Bingbot, Yeti)
- Disallow 경로 (admin, API, private media)
- Sitemap 위치 명시

### 5. 페이지 기능 확장 ✨ NEW
- **페이지네이션**: Django Paginator, 10개 페이지 번호 표시
- **검색 기능**: 제목/설명 검색
- **가격 필터**: 최소/최대 가격
- **할인율 필터**: 10%, 20%, 30%, 50% 이상
- **정렬**: 할인율/가격/최신/인기 순
- **페이지 크기**: 20/40/60/100개씩
- **필터 초기화**: 한번에 모든 필터 제거

### 6. 이미지 최적화 ✨ NEW
- **Lazy Loading**: Intersection Observer API
- **ImageOptimizer 서비스**:
  - WebP 변환 (80% 품질)
  - 리사이징 (max 1200x1200)
  - 썸네일 생성 (300x300)
  - 다중 크기 생성 (thumb, medium, original)
- **OG 이미지 URL**: WebP 우선 사용
- **Srcset 생성**: 반응형 이미지 (300w, 600w, 900w, 1200w)

### 7. SEO 분석 및 모니터링 ✨ NEW
- **SEOAnalyzer**:
  - 메타 태그 검증 (제목 30-60자, 설명 120-160자)
  - Schema.org 검증
  - 이미지 최적화 체크
  - 종합 점수 (A-F 등급)
- **SEOMonitor**:
  - 페이지 조회 추적
  - SEO 지표 조회 (30일)

---

## 아키텍처

```
apps/core/services/
├── seo.py                          # SEO 서비스 레이어 (460 lines)
│   ├── SEOMetaGenerator            # 메타 태그 생성
│   └── StructuredDataGenerator     # Schema.org 데이터 생성
├── image_optimizer.py              # 이미지 최적화 (280 lines)
│   ├── ImageOptimizer              # WebP 변환, 리사이징, 썸네일
│   ├── generate_og_image_url       # OG 이미지 URL 생성
│   └── generate_srcset             # 반응형 이미지
└── seo_analyzer.py                 # SEO 분석 (330 lines)
    ├── SEOAnalyzer                 # 메타/스키마/이미지 분석
    └── SEOMonitor                  # 성능 모니터링

apps/core/templatetags/
├── __init__.py
└── seo_tags.py                     # Django 템플릿 태그 (67 lines)
    ├── render_meta_tags            # 메타 태그 렌더링
    ├── render_structured_data      # JSON-LD 렌더링
    ├── json_ld                     # 직접 JSON-LD 출력
    └── truncate_seo                # SEO용 텍스트 자르기

templates/
├── seo/
│   ├── meta_tags.html              # 메타 태그 템플릿
│   └── structured_data.html        # JSON-LD 템플릿
├── base.html                       # SEO 태그 통합
└── frontend/
    ├── landing.html                # 랜딩 페이지 (페이지네이션, Lazy loading)
    └── home.html                   # 홈페이지

apps/products/
├── sitemaps.py                     # Sitemap 클래스 (3종)
└── views/frontend.py               # SEO + 페이지네이션 (190 lines)

static/
└── robots.txt                      # 크롤러 규칙
```

---

## API 및 사용법

### 1. SEOMetaGenerator 사용

#### 랜딩 페이지 메타 생성

```python
from apps.core.services.seo import SEOMetaGenerator

# View에서 사용
def landing_page(request, brand_slug, category_slug):
    # ... 상품 조회 ...
    
    seo_generator = SEOMetaGenerator(request)
    meta = seo_generator.generate_landing_page_meta(
        brand_name='노스페이스',
        category_name='다운',
        products=products,  # 할인율 계산용
        custom_description='커스텀 설명 (선택사항)'
    )
    
    # meta는 다음을 포함:
    # {
    #     'title': '노스페이스 다운 최대 70% 할인 특가 - E-wall',
    #     'description': '노스페이스 다운 이월 특가 최대 70% 할인...',
    #     'keywords': '노스페이스, 다운, 할인, 최저가...',
    #     'canonical_url': 'https://ewall.com/northface/down/',
    #     'og': {
    #         'title': '...',
    #         'description': '...',
    #         'type': 'website',
    #         'url': '...',
    #         'image': '...',
    #         'site_name': 'E-wall'
    #     },
    #     'twitter': {
    #         'card': 'summary_large_image',
    #         'title': '...',
    #         'description': '...',
    #         'image': '...'
    #     }
    # }
    
    return render(request, 'landing.html', {'meta': meta})
```

#### 상품 상세 메타 생성

```python
meta = seo_generator.generate_product_detail_meta(
    product=product,
    brand_name='노스페이스',
    category_name='다운'
)
# OG type='product', 상품 이미지 사용
```

#### 홈페이지 메타 생성

```python
meta = seo_generator.generate_home_meta()
# E-wall 기본 메타 태그
```

---

### 2. StructuredDataGenerator 사용

#### Product Schema 생성

```python
from apps.core.services.seo import StructuredDataGenerator

schema_generator = StructuredDataGenerator(request)
product_schema = schema_generator.generate_product_schema(product)

# 결과 (JSON-LD):
# {
#     "@context": "https://schema.org",
#     "@type": "Product",
#     "name": "노스페이스 다운 재킷",
#     "image": "https://...",
#     "description": "...",
#     "brand": {
#         "@type": "Brand",
#         "name": "노스페이스"
#     },
#     "offers": {
#         "@type": "Offer",
#         "url": "https://...",
#         "priceCurrency": "KRW",
#         "price": 350000,
#         "availability": "https://schema.org/InStock"
#     }
# }
```

#### CollectionPage Schema 생성

```python
collection_schema = schema_generator.generate_collection_page_schema(
    brand_name='노스페이스',
    category_name='다운',
    products=products  # 최대 10개만 포함
)

# ItemList 포함 (position 1-10)
```

#### Breadcrumb Schema 생성

```python
breadcrumb_schema = schema_generator.generate_breadcrumb_schema([
    {'name': '홈', 'url': '/'},
    {'name': '노스페이스', 'url': '/northface/'},
    {'name': '다운', 'url': '/northface/down/'}
])
```

#### Organization Schema 생성

```python
org_schema = schema_generator.generate_organization_schema()
# E-wall 회사 정보, 로고, 소셜 링크
```

---

### 3. Django Template Tags 사용

#### base.html에서 메타 태그 렌더링

```django
{% load seo_tags %}

<head>
    {% if meta %}
        {% render_meta_tags meta %}
    {% else %}
        <title>기본 제목</title>
    {% endif %}
</head>
```

#### Structured Data 렌더링

```django
{% load seo_tags %}

<head>
    {% if schemas %}
        {% render_structured_data schemas %}
    {% endif %}
</head>
```

#### 직접 JSON-LD 출력

```django
{% load seo_tags %}

<script type="application/ld+json">
{% json_ld product_schema %}
</script>
```

#### SEO 텍스트 자르기

```django
{% load seo_tags %}

{{ long_text|truncate_seo }}
<!-- 160자로 자르고, 단어 중간 자르지 않음, "..." 추가 -->
```

---

### 4. Frontend 뷰 통합 예시

```python
# apps/products/views/frontend.py

from apps.core.services.seo import SEOMetaGenerator, StructuredDataGenerator
import json

def landing_page(request, brand_slug, category_slug):
    # ... 브랜드, 카테고리, 상품 조회 ...
    
    # SEO 메타 생성
    seo_generator = SEOMetaGenerator(request)
    meta = seo_generator.generate_landing_page_meta(
        brand_name=brand.name,
        category_name=category.name,
        products=list(products)
    )
    
    # Schema.org 데이터 생성
    schema_generator = StructuredDataGenerator(request)
    schemas = [
        schema_generator.generate_collection_page_schema(
            brand_name=brand.name,
            category_name=category.name,
            products=list(products)[:10]
        ),
        schema_generator.generate_breadcrumb_schema([
            {'name': '홈', 'url': '/'},
            {'name': brand.name, 'url': f'/{brand_slug}/'},
            {'name': category.name, 'url': f'/{brand_slug}/{category_slug}/'}
        ]),
        schema_generator.generate_organization_schema()
    ]
    
    context = {
        'brand': brand,
        'category': category,
        'products': products,
        'meta': meta,
        'schemas': [json.dumps(s, ensure_ascii=False, indent=2) for s in schemas]
    }
    
    return render(request, 'frontend/landing.html', context)
```

---

## Sitemap 구성

### URL 구조

```
https://ewall.com/sitemap.xml
├── https://ewall.com/sitemap-landing.xml    # 랜딩 페이지
├── https://ewall.com/sitemap-products.xml   # 상품 상세
└── https://ewall.com/sitemap-images.xml     # 상품 이미지
```

### Sitemap 클래스

#### LandingPageSitemap

```python
# apps/products/sitemaps.py

class LandingPageSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = 'https'
    
    def items(self):
        # 브랜드×카테고리 조합
        return [
            {
                'brand_slug': 'northface',
                'category_slug': 'down',
                'lastmod': timezone.now()
            },
            # ...
        ]
    
    def location(self, item):
        return f"/landing/{item['brand_slug']}/{item['category_slug']}/"
```

#### ProductDetailSitemap

```python
class ProductDetailSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.6
    limit = 5000
    
    def items(self):
        return Product.objects.filter(is_active=True)
    
    def priority(self, obj):
        # 조회수 기반 우선순위
        if obj.view_count > 1000:
            return 0.9
        elif obj.view_count > 500:
            return 0.7
        return 0.6
```

#### ProductImageSitemap

```python
class ProductImageSitemap(Sitemap):
    changefreq = "monthly"
    priority = 0.5
    limit = 1000
    
    def items(self):
        return Product.objects.filter(
            is_active=True,
            image_url__isnull=False
        ).exclude(image_url='')[:1000]
```

---

## Robots.txt 설정

### 파일 위치
```
static/robots.txt
```

### 내용

```
User-agent: *
Allow: /
Disallow: /admin/
Disallow: /api/auth/
Disallow: /media/private/
Disallow: /*.json$
Disallow: /*?sort=*
Disallow: /*?page=*&

Allow: /static/
Allow: /media/products/
Allow: /api/products/
Allow: /landing/

Sitemap: https://ewall.com/sitemap.xml
Sitemap: https://ewall.com/sitemap-products.xml
Sitemap: https://ewall.com/sitemap-landing.xml

Crawl-delay: 1

User-agent: Googlebot
Crawl-delay: 0.5

User-agent: Bingbot
Crawl-delay: 1
```

### URL 라우팅

```python
# config/urls.py

from django.views.generic import TemplateView

urlpatterns = [
    # ...
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    ), name='robots'),
]
```

---

## 테스트

### 테스트 파일 구조

```
tests/
└── test_seo_services.py           # SEO 서비스 테스트
    ├── TestSEOMetaGenerator       # 메타 태그 생성 테스트
    ├── TestStructuredDataGenerator # 스키마 생성 테스트
    └── TestSEOIntegration         # 통합 테스트
```

### 테스트 실행

```bash
# 모든 SEO 테스트 실행
pytest tests/test_seo_services.py -v

# 특정 테스트 클래스만 실행
pytest tests/test_seo_services.py::TestSEOMetaGenerator -v

# 커버리지 포함
pytest tests/test_seo_services.py --cov=apps.core.services.seo
```

### 주요 테스트 케이스

#### 1. 메타 태그 생성 테스트

```python
def test_generate_landing_page_meta(mock_request, sample_products):
    generator = SEOMetaGenerator(mock_request)
    meta = generator.generate_landing_page_meta(
        brand_name='노스페이스',
        category_name='다운',
        products=sample_products
    )
    
    assert 'title' in meta
    assert '노스페이스' in meta['title']
    assert len(meta['description']) <= 160
    assert meta['og']['type'] == 'website'
```

#### 2. 스키마 생성 테스트

```python
def test_generate_product_schema(mock_request, sample_products):
    generator = StructuredDataGenerator(mock_request)
    schema = generator.generate_product_schema(sample_products[0])
    
    assert schema['@type'] == 'Product'
    assert 'offers' in schema
    assert schema['offers']['priceCurrency'] == 'KRW'
```

#### 3. 통합 테스트

```python
def test_landing_page_has_seo_meta(client, brand, category):
    response = client.get(f'/{brand.slug}/{category.slug}/')
    
    assert 'meta' in response.context
    assert 'schemas' in response.context
```

---

## 성능 최적화

### 1. 메타 생성 캐싱 (추천)

```python
from django.core.cache import cache

def landing_page(request, brand_slug, category_slug):
    cache_key = f"seo_meta:{brand_slug}:{category_slug}"
    meta = cache.get(cache_key)
    
    if not meta:
        seo_generator = SEOMetaGenerator(request)
        meta = seo_generator.generate_landing_page_meta(...)
        cache.set(cache_key, meta, 3600)  # 1시간 캐싱
    
    # ...
```

### 2. Sitemap 캐싱

```python
# Django settings.py
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
    }
}
```

### 3. Gzip 압축 (Sitemap)

```python
# settings.py
MIDDLEWARE = [
    'django.middleware.gzip.GZipMiddleware',
    # ...
]
```

---

## SEO 체크리스트

### ✅ 완료된 항목

- [x] OG 태그 (Facebook, LinkedIn)
- [x] Twitter Card 태그
- [x] Canonical URL
- [x] Meta description (160자 제한)
- [x] Keywords 생성
- [x] Product Schema
- [x] CollectionPage Schema
- [x] Breadcrumb Schema
- [x] Organization Schema
- [x] LandingPage Sitemap
- [x] ProductDetail Sitemap
- [x] ProductImage Sitemap
- [x] Robots.txt
- [x] Template tags
- [x] 유닛 테스트
- [x] **페이지네이션** (Django Paginator)
- [x] **검색 기능** (제목/설명)
- [x] **가격/할인율 필터**
- [x] **정렬 옵션** (5가지)
- [x] **Lazy Loading** (Intersection Observer)
- [x] **ImageOptimizer** (WebP, 리사이징, 썸네일)
- [x] **SEOAnalyzer** (메타/스키마/이미지 검증)
- [x] **SEOMonitor** (성능 모니터링)

### 🔜 향후 개선 사항

- [ ] Google Search Console 통합 (API)
- [ ] Sitemap ping (자동 제출)
- [ ] Structured data 검증 자동화
- [ ] Lighthouse CI 통합
- [ ] 실제 WebP 이미지 변환 (Pillow 설치 필요)
- [ ] CDN 통합
- [ ] AMP (Accelerated Mobile Pages)
- [ ] Preload/Prefetch 최적화
- [ ] Service Worker (PWA)

---

## 트러블슈팅

### 1. "Module seo_tags not found"

**원인**: apps.core가 INSTALLED_APPS에 없음

**해결**:
```python
# config/settings.py
INSTALLED_APPS = [
    # ...
    'apps.core',  # 추가
]
```

### 2. Sitemap이 404 에러

**원인**: URL 라우팅 누락

**해결**:
```python
# config/urls.py
from apps.products.sitemaps import (
    LandingPageSitemap,
    ProductDetailSitemap,
    ProductImageSitemap
)

sitemaps = {
    'landing': LandingPageSitemap,
    'products': ProductDetailSitemap,
    'images': ProductImageSitemap,
}

urlpatterns = [
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='sitemap'),
]
```

### 3. Schema 검증 실패

**해결**: Google Rich Results Test 사용
```
https://search.google.com/test/rich-results
```

### 4. Meta description이 잘림

**원인**: 160자 초과

**해결**: `truncate_seo` 필터 사용 또는 자동 제한 (이미 구현됨)

---

## 관련 문서

- [Django Sitemaps 공식 문서](https://docs.djangoproject.com/en/5.0/ref/contrib/sitemaps/)
- [Schema.org Product](https://schema.org/Product)
- [Open Graph Protocol](https://ogp.me/)
- [Twitter Cards](https://developer.twitter.com/en/docs/twitter-for-websites/cards/overview/abouts-cards)
- [Google Search Console](https://search.google.com/search-console)

---

## 변경 이력

| 날짜 | 버전 | 변경 내용 | 작성자 |
|------|------|-----------|--------|
| 2025-01-XX | 1.0.0 | 초기 구현 (Meta, Schema, Sitemap, Robots) | Dev Team |

---

## 라이센스

Internal Use Only - E-wall Project
