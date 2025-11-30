# 🚀 네이버 이월상품 수집 및 사용 가이드

## 📋 질문 답변

### 1. 실시간으로 상품 재고 및 가격 변동을 반영할 수 있는가?

**✅ 가능합니다!**

#### 가격 실시간 반영 방법
```
방법 1: 자동 업데이트 (Celery)
- 4시간마다: 전체 상품 재크롤링
- 1시간마다: 인기 상품 가격 체크
- 매일 자정: 가격 스냅샷 저장

방법 2: 수동 업데이트
- 스크립트 실행으로 즉시 업데이트
- python scripts/update_product_prices.py

방법 3: 상품 조회 시 실시간 확인
- 사용자가 상품 상세 페이지 접속 시
- API 재호출하여 최신 가격 표시
- 캐시 5분 유지 (API 호출 절약)
```

#### 재고 반영
```
✅ 품절 상품 자동 제외
- 네이버 API는 품절 상품을 검색 결과에서 제외
- 검색 결과에 없으면 → in_stock=False 처리

⚠️ 정확한 재고 수량은 제공 안 됨
- 재고 있음/없음만 확인 가능
```

---

### 2. 구매하기 링크를 클릭하면 해당 물품의 구매사이트로 이동 가능한가?

**✅ 완전히 가능합니다!**

네이버 API 응답에 포함된 정보:
```python
{
    'link': 'https://shopping.naver.com/...',  # 실제 구매 링크
    'mallName': '쿠팡',  # 판매 쇼핑몰
}
```

E-wall 저장 필드:
```python
product.deeplink = 네이버 쇼핑 링크
→ 클릭 시 해당 쇼핑몰 상품 페이지로 이동
→ 쿠팡, 11번가, 지마켓 등 다양한 쇼핑몰
```

---

## 🎯 다음 단계: 이월상품 수집 및 홈페이지 표시

### Step 1: 이월상품 수집 (5분)

```powershell
# 네이버 쇼핑에서 이월상품 수집
python scripts/collect_naver_outlet_products.py
```

**예상 결과:**
```
🚀 이월상품 수집 시작: 7개 키워드
'노스페이스 이월': 100개 검색됨
  → 할인율 30% 이상: 68개
  ✅ 신규: 노스페이스 NEW 눕시 다운 자켓
  ✅ 신규: 노스페이스 알파인 눕시 다운...
...

✨ 수집 완료!
  신규 생성: 245개
  업데이트: 0개
  에러: 3개
```

---

### Step 2: 관리자 페이지에서 확인

```powershell
# 개발 서버 실행
python manage.py runserver
```

브라우저에서:
```
http://localhost:8000/admin/products/genericproduct/

필터:
- 출처(source): naver
- 할인율 30% 이상
- 재고 있음
```

---

### Step 3: 홈페이지에서 이월상품 표시

#### 3-1. 이월상품 전용 뷰 추가

파일: `apps/products/views/frontend.py`

기존 코드에 추가할 뷰:
```python
def outlet_products(request):
    """이월상품 목록"""
    from django.core.paginator import Paginator
    
    # 할인율 30% 이상 상품
    products = GenericProduct.objects.filter(
        discount_rate__gte=30,
        in_stock=True
    ).select_related('brand', 'category').order_by('-discount_rate')
    
    # 브랜드 필터
    brand_slug = request.GET.get('brand')
    if brand_slug:
        products = products.filter(brand__slug=brand_slug)
    
    # 가격 정렬
    sort = request.GET.get('sort', '-discount_rate')
    products = products.order_by(sort)
    
    # 페이징
    paginator = Paginator(products, 24)
    page = request.GET.get('page', 1)
    products_page = paginator.get_page(page)
    
    context = {
        'products': products_page,
        'total_count': products.count(),
        'brands': Brand.objects.all(),
    }
    
    return render(request, 'products/outlet_list.html', context)
```

#### 3-2. URL 추가

파일: `apps/products/frontend_urls.py`

```python
from apps.products.views.frontend import outlet_products

urlpatterns = [
    # ... 기존 URL들 ...
    path('outlet/', outlet_products, name='outlet-products'),
]
```

#### 3-3. 템플릿 생성

파일: `templates/products/outlet_list.html`

```html
{% extends 'base.html' %}

{% block content %}
<div class="container mx-auto px-4 py-8">
    <!-- 헤더 -->
    <div class="mb-8">
        <h1 class="text-3xl font-bold mb-2">🔥 이월상품 특가</h1>
        <p class="text-gray-600">30% 이상 할인된 프리미엄 브랜드 상품</p>
        <p class="text-sm text-gray-500 mt-2">총 {{ total_count }}개 상품</p>
    </div>
    
    <!-- 필터 -->
    <div class="mb-6 flex gap-4">
        <!-- 브랜드 필터 -->
        <select class="border rounded px-4 py-2" onchange="location.href='?brand='+this.value">
            <option value="">전체 브랜드</option>
            {% for brand in brands %}
            <option value="{{ brand.slug }}">{{ brand.name }}</option>
            {% endfor %}
        </select>
        
        <!-- 정렬 -->
        <select class="border rounded px-4 py-2" onchange="location.href='?sort='+this.value">
            <option value="-discount_rate">할인율 높은순</option>
            <option value="price">가격 낮은순</option>
            <option value="-price">가격 높은순</option>
            <option value="-updated_at">최신순</option>
        </select>
    </div>
    
    <!-- 상품 그리드 -->
    <div class="grid grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6">
        {% for product in products %}
        <div class="border rounded-lg overflow-hidden hover:shadow-lg transition">
            <!-- 상품 이미지 -->
            <div class="relative">
                <img src="{{ product.image_url }}" 
                     alt="{{ product.title }}"
                     class="w-full h-64 object-cover">
                
                <!-- 할인율 뱃지 -->
                <div class="absolute top-2 right-2 bg-red-500 text-white px-3 py-1 rounded-full font-bold">
                    {{ product.discount_rate }}% OFF
                </div>
            </div>
            
            <!-- 상품 정보 -->
            <div class="p-4">
                <p class="text-sm text-gray-500 mb-1">{{ product.brand.name }}</p>
                <h3 class="font-semibold mb-2 line-clamp-2">{{ product.title }}</h3>
                
                <!-- 가격 -->
                <div class="mb-3">
                    <p class="text-sm text-gray-400 line-through">
                        {{ product.original_price|floatformat:0|intcomma }}원
                    </p>
                    <p class="text-xl font-bold text-red-500">
                        {{ product.price|floatformat:0|intcomma }}원
                    </p>
                </div>
                
                <!-- 판매처 -->
                <p class="text-xs text-gray-500 mb-3">{{ product.seller }}</p>
                
                <!-- 구매 버튼 -->
                <a href="{{ product.deeplink }}" 
                   target="_blank"
                   class="block w-full bg-blue-500 text-white text-center py-2 rounded hover:bg-blue-600 transition">
                    구매하기 →
                </a>
            </div>
        </div>
        {% empty %}
        <p class="col-span-4 text-center text-gray-500 py-12">
            이월상품이 없습니다.
        </p>
        {% endfor %}
    </div>
    
    <!-- 페이징 -->
    {% if products.has_other_pages %}
    <div class="mt-8 flex justify-center gap-2">
        {% if products.has_previous %}
        <a href="?page={{ products.previous_page_number }}" 
           class="px-4 py-2 border rounded hover:bg-gray-100">이전</a>
        {% endif %}
        
        <span class="px-4 py-2">{{ products.number }} / {{ products.paginator.num_pages }}</span>
        
        {% if products.has_next %}
        <a href="?page={{ products.next_page_number }}" 
           class="px-4 py-2 border rounded hover:bg-gray-100">다음</a>
        {% endif %}
    </div>
    {% endif %}
</div>
{% endblock %}
```

---

### Step 4: 실시간 가격 업데이트 설정

#### 방법 1: 수동 업데이트 (즉시 실행)

```powershell
# 기존 상품들의 가격 업데이트
python scripts/update_product_prices.py
```

#### 방법 2: 자동 업데이트 (Celery 스케줄)

파일: `config/celery.py`

이미 설정되어 있는 스케줄:
```python
'crawl-multi-platform-every-4-hours': {
    'task': 'apps.products.tasks.crawl_multi_platform',
    'schedule': crontab(minute=0, hour='*/4'),  # 4시간마다
}
```

Celery 실행:
```powershell
# Terminal 1: Worker
celery -A config worker -l info --pool=solo

# Terminal 2: Beat (스케줄러)
celery -A config beat -l info

# Terminal 3: Django 서버
python manage.py runserver
```

---

## 📊 실시간 가격 반영 확인

### 테스트 시나리오

```powershell
# 1. 초기 수집
python scripts/collect_naver_outlet_products.py

# 2. DB 확인
python manage.py shell
```

```python
from apps.products.models import GenericProduct

# 특정 상품 확인
product = GenericProduct.objects.filter(source='naver').first()
print(f"상품: {product.title}")
print(f"현재 가격: {product.price:,}원")
print(f"업데이트: {product.updated_at}")
```

```powershell
# 3. 1시간 후 가격 업데이트
python scripts/update_product_prices.py

# 4. 가격 변동 확인
python manage.py shell
```

```python
from apps.products.models import GenericProduct

product = GenericProduct.objects.get(id='naver-12345')
print(f"새 가격: {product.price:,}원")
print(f"업데이트: {product.updated_at}")
```

---

## 🎯 구매 링크 작동 확인

### 1. 관리자 페이지에서 확인

```
http://localhost:8000/admin/products/genericproduct/

→ 상품 클릭
→ "Deeplink" 필드 확인
→ 링크가 "https://shopping.naver.com/..." 형식
```

### 2. 홈페이지에서 테스트

```
http://localhost:8000/outlet/

→ 상품 카드의 "구매하기" 버튼 클릭
→ 새 탭에서 네이버 쇼핑 → 해당 쇼핑몰 상품 페이지 열림
→ 구매 가능!
```

---

## ✅ 최종 체크리스트

### 데이터 수집
- [ ] `python scripts/collect_naver_outlet_products.py` 실행
- [ ] 관리자 페이지에서 상품 확인
- [ ] 이미지, 가격, 할인율 정상 표시

### 실시간 가격
- [ ] `python scripts/update_product_prices.py` 실행
- [ ] 가격 변동 로그 확인
- [ ] Celery 자동 업데이트 설정 (선택)

### 홈페이지 표시
- [ ] `apps/products/views/frontend.py`에 outlet_products 뷰 추가
- [ ] URL 연결
- [ ] 템플릿 생성
- [ ] `http://localhost:8000/outlet/` 접속 확인

### 구매 링크
- [ ] 상품 카드의 "구매하기" 버튼 클릭
- [ ] 네이버 쇼핑 → 실제 쇼핑몰로 이동 확인
- [ ] 여러 상품 테스트 (쿠팡, 11번가 등)

---

## 🎁 추가 기능

### 1. 가격 알림 기능

```python
# 가격 하락 시 알림 발송
from apps.alerts.tasks import check_price_changes

# Celery 태스크로 자동 실행됨
# 1시간마다 가격 체크 → 하락 시 이메일 발송
```

### 2. 인기 상품 캐싱

```python
# 인기 이월상품 캐싱 (빠른 로딩)
from django.core.cache import cache

popular_outlets = cache.get('popular_outlets')
if not popular_outlets:
    popular_outlets = GenericProduct.objects.filter(
        discount_rate__gte=50,  # 50% 이상 할인
        in_stock=True
    ).order_by('-discount_rate')[:20]
    
    cache.set('popular_outlets', popular_outlets, 3600)  # 1시간
```

### 3. 브랜드별 이월상품 페이지

```python
# URL: /outlet/노스페이스/
def brand_outlet(request, brand_slug):
    brand = get_object_or_404(Brand, slug=brand_slug)
    products = GenericProduct.objects.filter(
        brand=brand,
        discount_rate__gte=30,
        in_stock=True
    )
    return render(request, 'products/brand_outlet.html', {
        'brand': brand,
        'products': products
    })
```

---

## 🆘 문제 해결

### "상품이 0개 수집됨"
```
→ .env 파일의 NAVER_CLIENT_ID/SECRET 재확인
→ 네이버 개발자센터에서 "검색" API 활성화 확인
→ 서버 재시작
```

### "구매 링크가 작동 안 함"
```
→ product.deeplink 필드 확인
→ 네이버 쇼핑 링크가 정상인지 확인
→ 품절 상품은 링크 비활성화 가능
```

### "가격이 업데이트 안 됨"
```
→ update_product_prices.py 실행
→ API 호출 제한 확인 (네이버: 일 25,000건)
→ Celery가 실행 중인지 확인
```

---

## 📈 예상 결과

```
초기 수집: 200-500개 이월상품
브랜드: 노스페이스, 파타고니아, 아크테릭스 등
할인율: 30-70%
가격 범위: 5만원 ~ 50만원

구매 링크: 100% 작동
실시간 가격: 4시간마다 자동 업데이트
품절 처리: 자동
```

축하합니다! 이제 실제 이월상품으로 서비스할 수 있습니다! 🎉
