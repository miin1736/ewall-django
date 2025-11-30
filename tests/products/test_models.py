"""
Product model tests
"""
import pytest
from decimal import Decimal
from apps.core.models import Brand, Category
from apps.products.models import DownProduct


@pytest.fixture
def brand():
    return Brand.objects.create(name='TestBrand', slug='testbrand')


@pytest.fixture
def category():
    return Category.objects.create(
        name='Down', 
        slug='down', 
        category_type='down'
    )


@pytest.mark.django_db
class TestDownProduct:
    """다운 상품 모델 테스트"""
    
    def test_create_down_product(self, brand, category):
        """다운 상품 생성 테스트"""
        product = DownProduct.objects.create(
            id='test-001',
            brand=brand,
            category=category,
            title='Test Down Jacket 800FP 90/10',
            slug='test-down-jacket',
            image_url='https://example.com/image.jpg',
            price=Decimal('100000'),
            original_price=Decimal('150000'),
            discount_rate=Decimal('33.33'),
            seller='Test Seller',
            deeplink='https://example.com/product',
            source='test',
            down_type='goose',
            down_ratio='90-10',
            fill_power=800,
            hood=False,
            fit='regular',
            shell='nylon'
        )
        
        assert product.id == 'test-001'
        assert product.down_ratio == '90-10'
        assert product.fill_power == 800
        assert product.discount_rate == Decimal('33.33')
    
    def test_product_string_representation(self, brand, category):
        """상품 문자열 표현 테스트"""
        product = DownProduct.objects.create(
            id='test-002',
            brand=brand,
            category=category,
            title='Test Product',
            slug='test-product',
            image_url='https://example.com/image.jpg',
            price=Decimal('50000'),
            original_price=Decimal('100000'),
            discount_rate=Decimal('50'),
            seller='Test',
            deeplink='https://example.com',
            source='test'
        )
        
        assert str(product) == 'Test Product'
