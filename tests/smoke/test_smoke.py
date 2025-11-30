"""
Smoke tests for critical functionality
"""
import pytest
from django.test import Client
from apps.core.models import Brand, Category


@pytest.fixture
def client():
    return Client()


@pytest.fixture
def setup_data():
    """테스트 데이터 설정"""
    brand = Brand.objects.create(name='TestBrand', slug='testbrand')
    category = Category.objects.create(name='Down', slug='down', category_type='down')
    return brand, category


@pytest.mark.django_db
class TestSmokeTests:
    """스모크 테스트"""
    
    def test_home_page_loads(self, client):
        """홈페이지 로드 테스트"""
        response = client.get('/')
        assert response.status_code == 200
    
    def test_api_product_list_endpoint(self, client, setup_data):
        """상품 목록 API 테스트"""
        brand, category = setup_data
        response = client.get(f'/api/products/{brand.slug}/{category.slug}/')
        
        assert response.status_code == 200
        data = response.json()
        assert 'products' in data
        assert 'total' in data
    
    def test_alert_create_api(self, client, setup_data):
        """알림 생성 API 테스트"""
        brand, category = setup_data
        
        payload = {
            'email': 'test@example.com',
            'brand_slug': brand.slug,
            'category_slug': category.slug,
            'conditions': {
                'priceBelow': 100000,
                'discountAtLeast': 30
            }
        }
        
        response = client.post(
            '/api/alerts/',
            data=payload,
            content_type='application/json'
        )
        
        assert response.status_code == 201
        data = response.json()
        assert data['email'] == 'test@example.com'
    
    def test_sitemap_loads(self, client):
        """사이트맵 로드 테스트"""
        response = client.get('/sitemap.xml')
        assert response.status_code == 200
