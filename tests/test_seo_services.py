"""
SEO Services 테스트
"""
import pytest
from django.test import RequestFactory
from apps.core.services.seo import SEOMetaGenerator, StructuredDataGenerator
from apps.core.models import Brand, Category
from apps.products.models import DownProduct


@pytest.fixture
def request_factory():
    """Request factory"""
    return RequestFactory()


@pytest.fixture
def mock_request(request_factory):
    """Mock HTTP request"""
    request = request_factory.get('/')
    request.META['HTTP_HOST'] = 'ewall.com'
    request.scheme = 'https'
    return request


@pytest.fixture
def brand():
    """브랜드 fixture"""
    return Brand.objects.create(
        name='노스페이스',
        slug='northface'
    )


@pytest.fixture
def category():
    """카테고리 fixture"""
    return Category.objects.create(
        name='다운',
        slug='down'
    )


@pytest.fixture
def sample_products(brand, category):
    """샘플 상품 데이터"""
    products = []
    for i in range(3):
        product = DownProduct.objects.create(
            id=f'test-product-{i+1}',
            brand=brand,
            category=category,
            title=f'노스페이스 다운 {i+1}',
            slug=f'north-face-down-{i+1}',
            deeplink=f'https://example.com/product/{i+1}',
            image_url=f'https://example.com/image/{i+1}.jpg',
            original_price=500000,
            price=350000 - (i * 20000),
            discount_rate=30 + (i * 5),
            seller='Test Seller',
            in_stock=True,
            down_ratio='90/10',
            fill_power=800,
            hood=True,
            fit='regular',
            shell='nylon'
        )
        products.append(product)
    return products


@pytest.mark.django_db
class TestSEOMetaGenerator:
    """SEO Meta 태그 생성 테스트"""
    
    def test_generate_landing_page_meta(self, mock_request, sample_products):
        """랜딩 페이지 메타 태그 생성"""
        generator = SEOMetaGenerator(mock_request)
        
        meta = generator.generate_landing_page_meta(
            brand_name='노스페이스',
            category_name='다운',
            products=sample_products
        )
        
        # 기본 구조 검증
        assert 'title' in meta
        assert 'description' in meta
        assert 'keywords' in meta
        assert 'canonical_url' in meta
        assert 'og' in meta
        assert 'twitter' in meta
        
        # 제목 검증
        assert '노스페이스' in meta['title']
        assert '다운' in meta['title']
        
        # 설명 길이 검증 (160자 제한)
        assert len(meta['description']) <= 160
        
        # OG 태그 검증
        assert meta['og']['title'] == meta['title']
        assert meta['og']['type'] == 'website'
        assert 'ewall.com' in meta['og']['url']
        
        # Twitter Card 검증
        assert meta['twitter']['card'] == 'summary_large_image'
        assert meta['twitter']['title'] == meta['title']
    
    def test_generate_landing_page_meta_with_discount(self, mock_request, sample_products):
        """할인율이 포함된 메타 태그 생성"""
        generator = SEOMetaGenerator(mock_request)
        
        meta = generator.generate_landing_page_meta(
            brand_name='노스페이스',
            category_name='다운',
            products=sample_products
        )
        
        # 최대 할인율이 설명에 포함되어야 함
        max_discount = max(p.discount_rate for p in sample_products)
        assert str(int(max_discount)) in meta['description'] or '할인' in meta['description']
    
    def test_generate_product_detail_meta(self, mock_request, sample_products):
        """상품 상세 메타 태그 생성"""
        generator = SEOMetaGenerator(mock_request)
        product = sample_products[0]
        
        meta = generator.generate_product_detail_meta(
            product=product,
            brand_name='노스페이스',
            category_name='다운'
        )
        
        # 기본 구조 검증
        assert 'title' in meta
        assert 'description' in meta
        assert 'og' in meta
        
        # 상품명이 제목에 포함
        assert product.title in meta['title']
        
        # OG 이미지가 상품 이미지
        assert meta['og']['image'] == product.image_url
        assert meta['og']['type'] == 'product'
    
    def test_generate_home_meta(self, mock_request):
        """홈페이지 메타 태그 생성"""
        generator = SEOMetaGenerator(mock_request)
        
        meta = generator.generate_home_meta()
        
        # 기본 구조 검증
        assert 'title' in meta
        assert 'description' in meta
        assert 'keywords' in meta
        
        # E-wall 브랜드 포함
        assert 'E-wall' in meta['title'] or 'Ewall' in meta['title']
    
    def test_meta_description_length_limit(self, mock_request, sample_products):
        """메타 설명 길이 제한 테스트"""
        generator = SEOMetaGenerator(mock_request)
        
        # 긴 커스텀 설명
        long_description = "이것은 매우 긴 설명입니다. " * 20
        
        meta = generator.generate_landing_page_meta(
            brand_name='노스페이스',
            category_name='다운',
            products=sample_products,
            custom_description=long_description
        )
        
        # 160자 제한 검증
        assert len(meta['description']) <= 160


@pytest.mark.django_db
class TestStructuredDataGenerator:
    """Schema.org 구조화 데이터 생성 테스트"""
    
    def test_generate_product_schema(self, mock_request, sample_products):
        """상품 스키마 생성"""
        generator = StructuredDataGenerator(mock_request)
        product = sample_products[0]
        
        schema = generator.generate_product_schema(product)
        
        # Schema.org 기본 구조
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'Product'
        
        # 필수 필드
        assert schema['name'] == product.title
        assert schema['description']
        assert schema['image'] == product.image_url
        
        # Offer 정보
        assert 'offers' in schema
        offer = schema['offers']
        assert offer['@type'] == 'Offer'
        assert offer['price'] == float(product.price)
        assert offer['priceCurrency'] == 'KRW'
        assert offer['availability'] == 'https://schema.org/InStock'
        assert offer['url'] == product.deeplink
        
        # 브랜드 정보
        assert 'brand' in schema
        assert schema['brand']['@type'] == 'Brand'
        assert schema['brand']['name'] == product.brand.name
    
    def test_generate_collection_page_schema(self, mock_request, sample_products):
        """컬렉션 페이지 스키마 생성"""
        generator = StructuredDataGenerator(mock_request)
        
        schema = generator.generate_collection_page_schema(
            brand_name='노스페이스',
            category_name='다운',
            products=sample_products
        )
        
        # Schema.org 기본 구조
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'CollectionPage'
        
        # 필수 필드
        assert '노스페이스' in schema['name']
        assert '다운' in schema['name']
        assert 'ewall.com' in schema['url']
        
        # ItemList (최대 10개)
        assert 'mainEntity' in schema
        item_list = schema['mainEntity']
        assert item_list['@type'] == 'ItemList'
        assert len(item_list['itemListElement']) <= 10
        assert len(item_list['itemListElement']) == len(sample_products)
        
        # 첫 번째 아이템 검증
        first_item = item_list['itemListElement'][0]
        assert first_item['@type'] == 'ListItem'
        assert first_item['position'] == 1
        assert 'item' in first_item
    
    def test_generate_breadcrumb_schema(self, mock_request):
        """Breadcrumb 스키마 생성"""
        generator = StructuredDataGenerator(mock_request)
        
        breadcrumbs = [
            {'name': '홈', 'url': '/'},
            {'name': '노스페이스', 'url': '/northface/'},
            {'name': '다운', 'url': '/northface/down/'}
        ]
        
        schema = generator.generate_breadcrumb_schema(breadcrumbs)
        
        # Schema.org 기본 구조
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'BreadcrumbList'
        
        # ItemList 검증
        assert 'itemListElement' in schema
        assert len(schema['itemListElement']) == 3
        
        # 각 아이템 검증
        for i, item in enumerate(schema['itemListElement']):
            assert item['@type'] == 'ListItem'
            assert item['position'] == i + 1
            assert 'name' in item
            assert 'item' in item
    
    def test_generate_organization_schema(self, mock_request):
        """Organization 스키마 생성"""
        generator = StructuredDataGenerator(mock_request)
        
        schema = generator.generate_organization_schema()
        
        # Schema.org 기본 구조
        assert schema['@context'] == 'https://schema.org'
        assert schema['@type'] == 'Organization'
        
        # 필수 필드
        assert schema['name'] == 'E-wall'
        assert 'ewall.com' in schema['url']
        assert 'logo' in schema
        
        # Social 링크
        assert 'sameAs' in schema
        assert len(schema['sameAs']) > 0
    
    def test_collection_schema_limits_products(self, mock_request, sample_products):
        """컬렉션 스키마가 상품을 10개로 제한하는지 테스트"""
        generator = StructuredDataGenerator(mock_request)
        
        # 15개 상품 생성
        many_products = sample_products * 5  # 15개
        
        schema = generator.generate_collection_page_schema(
            brand_name='노스페이스',
            category_name='다운',
            products=many_products
        )
        
        # 최대 10개만 포함
        assert len(schema['mainEntity']['itemListElement']) == 10


@pytest.mark.django_db
class TestSEOIntegration:
    """SEO 통합 테스트"""
    
    def test_landing_page_has_seo_meta(self, client, brand, category):
        """랜딩 페이지에 SEO 메타 태그가 포함되는지 테스트"""
        response = client.get(f'/{brand.slug}/{category.slug}/')
        
        assert response.status_code == 200
        assert 'meta' in response.context
        assert 'schemas' in response.context
        
        # 메타 데이터 검증
        meta = response.context['meta']
        assert 'title' in meta
        assert 'description' in meta
        assert 'og' in meta
    
    def test_home_page_has_seo_meta(self, client):
        """홈페이지에 SEO 메타 태그가 포함되는지 테스트"""
        response = client.get('/')
        
        assert response.status_code == 200
        assert 'meta' in response.context
        assert 'schemas' in response.context
        
        # 메타 데이터 검증
        meta = response.context['meta']
        assert 'title' in meta
        assert 'E-wall' in meta['title'] or 'Ewall' in meta['title']
