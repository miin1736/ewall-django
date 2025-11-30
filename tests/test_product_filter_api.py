"""
Product Filter API Integration Tests
고급 필터링 API 통합 테스트

Coverage:
- 12+ 필터 조건 조합 시나리오
- 캐싱 동작 검증
- 성능 벤치마크 (500+ 상품 기준 200ms 이내)
- 필터 메타데이터 검증
"""
import pytest
import time
from django.urls import reverse
from django.core.cache import cache
from rest_framework.test import APIClient
from apps.core.models import Brand, Category
from apps.products.models import DownProduct


@pytest.mark.django_db
class TestProductFilterAPI:
    """상품 필터 API 통합 테스트"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """각 테스트 전 캐시 초기화"""
        cache.clear()
        self.client = APIClient()
    
    @pytest.fixture
    def brand_category(self):
        """브랜드, 카테고리 픽스처"""
        brand = Brand.objects.create(
            name="노스페이스",
            slug="northface",
            logo_url="https://example.com/logo.png"
        )
        category = Category.objects.create(
            name="다운",
            slug="down",
            category_type="down"
        )
        return brand, category
    
    @pytest.fixture
    def sample_down_products(self, brand_category):
        """샘플 다운 제품 50개 생성"""
        brand, category = brand_category
        products = []
        
        # 다양한 조합 생성
        down_ratios = ['90/10', '80/20', '70/30']
        fill_powers = [700, 750, 800, 850, 900]
        hoods = [True, False]
        fits = ['regular', 'slim', 'oversized']
        shells = ['nylon', 'polyester']
        
        for i in range(50):
            product = DownProduct.objects.create(
                id=f"prod_{i+1}",
                title=f"다운 재킷 {i+1}",
                slug=f"down-jacket-{i+1}",
                brand=brand,
                category=category,
                price=100000 + (i * 5000),
                original_price=200000 + (i * 5000),
                discount_rate=30 + (i % 40),
                image_url=f"https://example.com/product{i}.jpg",
                deeplink=f"https://example.com/p/{i}",
                seller="테스트셀러",
                source="coupang",
                in_stock=True,
                
                # 다운 전용 필드
                down_ratio=down_ratios[i % len(down_ratios)],
                fill_power=fill_powers[i % len(fill_powers)],
                hood=hoods[i % len(hoods)],
                fit=fits[i % len(fits)],
                shell=shells[i % len(shells)],
                down_type='goose' if i % 2 == 0 else 'duck'
            )
            products.append(product)
        
        return products
    
    def test_basic_product_list(self, brand_category, sample_down_products):
        """기본 상품 목록 조회 (필터 없음)"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'products' in response.data
        assert 'total' in response.data
        assert 'filters_applied' in response.data
        assert 'available_filters' in response.data
        assert response.data['total'] == 50
        assert len(response.data['products']) == 20  # 기본 page_size
    
    def test_filter_by_down_ratio(self, brand_category, sample_down_products):
        """다운비율 필터 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url, {'downRatio': '90/10'})
        
        assert response.status_code == 200
        assert response.data['filters_applied']['downRatio'] == '90/10'
        
        # 모든 상품이 90/10 다운비율인지 확인
        for product in response.data['products']:
            # Product 모델에서 확인
            db_product = DownProduct.objects.get(pk=product['id'])
            assert db_product.down_ratio == '90/10'
    
    def test_filter_by_fill_power_range(self, brand_category, sample_down_products):
        """필파워 범위 필터 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url, {
            'fillPowerMin': 800,
            'fillPowerMax': 900
        })
        
        assert response.status_code == 200
        assert response.data['filters_applied']['fillPowerMin'] == '800'
        assert response.data['filters_applied']['fillPowerMax'] == '900'
        
        # 모든 상품이 800-900 범위인지 확인
        for product in response.data['products']:
            db_product = DownProduct.objects.get(pk=product['id'])
            assert 800 <= db_product.fill_power <= 900
    
    def test_filter_by_hood(self, brand_category, sample_down_products):
        """후드 필터 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url, {'hood': 'true'})
        
        assert response.status_code == 200
        assert response.data['filters_applied']['hood'] == 'true'
        
        # 모든 상품이 후드 있는지 확인
        for product in response.data['products']:
            db_product = DownProduct.objects.get(pk=product['id'])
            assert db_product.hood is True
    
    def test_combined_filters(self, brand_category, sample_down_products):
        """복합 필터 테스트 (다운비율 + 필파워 + 후드 + 핏)"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url, {
            'downRatio': '90/10',
            'fillPowerMin': 800,
            'hood': 'true',
            'fit': 'slim',
            'priceMax': 300000,
            'discountMin': 50
        })
        
        assert response.status_code == 200
        
        # 모든 필터가 적용되었는지 확인
        filters = response.data['filters_applied']
        assert filters['downRatio'] == '90/10'
        assert filters['fillPowerMin'] == '800'
        assert filters['hood'] == 'true'
        assert filters['fit'] == 'slim'
        assert filters['priceMax'] == '300000'
        assert filters['discountMin'] == '50'
        
        # 실제 상품이 모든 조건 만족하는지 확인
        for product in response.data['products']:
            db_product = DownProduct.objects.get(pk=product['id'])
            assert db_product.down_ratio == '90/10'
            assert db_product.fill_power >= 800
            assert db_product.hood is True
            assert db_product.fit == 'slim'
            assert db_product.price <= 300000
            assert db_product.discount_rate >= 50
    
    def test_multiple_values_filter(self, brand_category, sample_down_products):
        """다중 값 필터 테스트 (쉼표 구분)"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url, {
            'fit': 'slim,regular',
            'shell': 'nylon,polyester'
        })
        
        assert response.status_code == 200
        
        # 모든 상품이 허용된 값 중 하나인지 확인
        for product in response.data['products']:
            db_product = DownProduct.objects.get(pk=product['id'])
            assert db_product.fit in ['slim', 'regular']
            assert db_product.shell in ['nylon', 'polyester']
    
    def test_sorting(self, brand_category, sample_down_products):
        """정렬 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        # 할인율 정렬 (기본)
        response = self.client.get(url, {'sort': 'discount'})
        assert response.status_code == 200
        products = response.data['products']
        discount_rates = [DownProduct.objects.get(pk=p['id']).discount_rate for p in products]
        assert discount_rates == sorted(discount_rates, reverse=True)
        
        # 낮은 가격순
        response = self.client.get(url, {'sort': 'price-low'})
        products = response.data['products']
        prices = [DownProduct.objects.get(pk=p['id']).price for p in products]
        assert prices == sorted(prices)
        
        # 높은 가격순
        response = self.client.get(url, {'sort': 'price-high'})
        products = response.data['products']
        prices = [DownProduct.objects.get(pk=p['id']).price for p in products]
        assert prices == sorted(prices, reverse=True)
    
    def test_pagination(self, brand_category, sample_down_products):
        """페이지네이션 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        # 1페이지 (20개)
        response = self.client.get(url, {'page': 1, 'page_size': 20})
        assert response.status_code == 200
        assert response.data['page'] == 1
        assert response.data['total'] == 50
        assert response.data['total_pages'] == 3
        assert len(response.data['products']) == 20
        
        # 2페이지
        response = self.client.get(url, {'page': 2, 'page_size': 20})
        assert len(response.data['products']) == 20
        
        # 3페이지 (마지막 10개)
        response = self.client.get(url, {'page': 3, 'page_size': 20})
        assert len(response.data['products']) == 10
    
    def test_available_filters_metadata(self, brand_category, sample_down_products):
        """사용 가능한 필터 메타데이터 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        available = response.data['available_filters']
        
        # 다운비율 옵션 확인
        assert 'downRatio' in available
        assert set(available['downRatio']) == {'90/10', '80/20', '70/30'}
        
        # 필파워 범위 확인
        assert 'fillPower' in available
        assert available['fillPower']['min'] == 700
        assert available['fillPower']['max'] == 900
        
        # 핏 옵션 확인
        assert 'fit' in available
        assert set(available['fit']) == {'regular', 'slim', 'oversized'}
    
    def test_price_discount_range_metadata(self, brand_category, sample_down_products):
        """가격/할인율 범위 메타데이터 테스트"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response = self.client.get(url)
        
        assert response.status_code == 200
        assert 'price_range' in response.data
        assert 'discount_range' in response.data
        
        # 실제 최소/최대 값과 일치하는지 확인
        min_price = min(p.price for p in sample_down_products)
        max_price = max(p.price for p in sample_down_products)
        assert response.data['price_range']['min'] == min_price
        assert response.data['price_range']['max'] == max_price
    
    def test_caching(self, brand_category, sample_down_products):
        """캐싱 동작 검증"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        # 첫 번째 요청 (캐시 미스)
        start = time.time()
        response1 = self.client.get(url, {'downRatio': '90/10'})
        time1 = time.time() - start
        
        # 두 번째 요청 (캐시 히트)
        start = time.time()
        response2 = self.client.get(url, {'downRatio': '90/10'})
        time2 = time.time() - start
        
        # 응답 동일 확인
        assert response1.data == response2.data
        
        # 캐시 히트가 더 빠른지 확인
        assert time2 < time1
        print(f"Cache miss: {time1:.4f}s, Cache hit: {time2:.4f}s")
    
    def test_different_filters_different_cache(self, brand_category, sample_down_products):
        """필터가 다르면 다른 캐시 키 사용"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        response1 = self.client.get(url, {'downRatio': '90/10'})
        response2 = self.client.get(url, {'downRatio': '80/20'})
        
        # 결과가 다른지 확인
        assert response1.data != response2.data
        assert response1.data['filters_applied']['downRatio'] == '90/10'
        assert response2.data['filters_applied']['downRatio'] == '80/20'
    
    @pytest.mark.benchmark
    def test_performance_500_products(self, brand_category):
        """성능 벤치마크: 500+ 상품 기준 200ms 이내"""
        brand, category = brand_category
        
        # 500개 상품 생성
        products = []
        for i in range(500):
            product = DownProduct.objects.create(
                id=f"bench_{i+1}",
                title=f"벤치마크 상품 {i+1}",
                slug=f"benchmark-product-{i+1}",
                brand=brand,
                category=category,
                price=100000 + (i * 1000),
                original_price=200000 + (i * 1000),
                discount_rate=30 + (i % 40),
                image_url=f"https://example.com/p{i}.jpg",
                deeplink=f"https://example.com/p/{i}",
                seller="테스트셀러",
                source="coupang",
                in_stock=True,
                
                down_ratio=['90/10', '80/20', '70/30'][i % 3],
                fill_power=[700, 750, 800, 850, 900][i % 5],
                hood=(i % 2 == 0),
                fit=['regular', 'slim', 'oversized'][i % 3],
                shell=['nylon', 'polyester'][i % 2],
                down_type='goose' if i % 2 == 0 else 'duck'
            )
            products.append(product)
        
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        # 복합 필터 성능 측정
        start = time.time()
        response = self.client.get(url, {
            'downRatio': '90/10',
            'fillPowerMin': 800,
            'hood': 'true',
            'fit': 'slim',
            'priceMax': 400000,
            'sort': 'discount'
        })
        elapsed = time.time() - start
        
        assert response.status_code == 200
        assert elapsed < 0.2, f"Performance degraded: {elapsed:.4f}s > 0.2s"
        print(f"Filtered 500 products in {elapsed:.4f}s")
    
    def test_no_results(self, brand_category, sample_down_products):
        """필터 결과 없음 처리"""
        brand, category = brand_category
        url = reverse('product-list', kwargs={
            'brand_slug': brand.slug,
            'category_slug': category.slug
        })
        
        # 불가능한 조건 (존재하지 않는 다운비율)
        response = self.client.get(url, {'downRatio': '95/5'})
        
        assert response.status_code == 200
        assert response.data['total'] == 0
        assert len(response.data['products']) == 0
        assert response.data['filters_applied']['downRatio'] == '95/5'
    
    def test_invalid_brand_or_category(self):
        """잘못된 브랜드/카테고리 슬러그"""
        url = reverse('product-list', kwargs={
            'brand_slug': 'nonexistent',
            'category_slug': 'down'
        })
        
        response = self.client.get(url)
        assert response.status_code == 404
