"""
Alert matcher tests
"""
import pytest
from decimal import Decimal
from apps.alerts.services.matcher import AlertMatcher
from apps.products.models import DownProduct
from apps.core.models import Brand, Category


@pytest.fixture
def brand():
    return Brand.objects.create(name='TestBrand', slug='testbrand')


@pytest.fixture
def category():
    return Category.objects.create(name='Down', slug='down', category_type='down')


@pytest.mark.django_db
class TestAlertMatcher:
    """알림 매칭 테스트"""
    
    def test_price_matching(self, brand, category):
        """가격 조건 매칭 테스트"""
        product = DownProduct(
            id='test-001',
            brand=brand,
            category=category,
            title='Test',
            slug='test',
            image_url='https://test.com',
            price=Decimal('89000'),
            original_price=Decimal('129000'),
            discount_rate=Decimal('31'),
            seller='Test',
            deeplink='https://test.com',
            source='test'
        )
        
        conditions = {'priceBelow': 100000}
        matcher = AlertMatcher()
        
        assert matcher.matches(product, conditions) == True
        
        conditions = {'priceBelow': 80000}
        assert matcher.matches(product, conditions) == False
    
    def test_discount_matching(self, brand, category):
        """할인율 조건 매칭 테스트"""
        product = DownProduct(
            id='test-002',
            brand=brand,
            category=category,
            title='Test',
            slug='test',
            image_url='https://test.com',
            price=Decimal('70000'),
            original_price=Decimal('100000'),
            discount_rate=Decimal('30'),
            seller='Test',
            deeplink='https://test.com',
            source='test'
        )
        
        conditions = {'discountAtLeast': 25}
        matcher = AlertMatcher()
        
        assert matcher.matches(product, conditions) == True
        
        conditions = {'discountAtLeast': 35}
        assert matcher.matches(product, conditions) == False
    
    def test_down_attributes_matching(self, brand, category):
        """다운 속성 조건 매칭 테스트"""
        product = DownProduct(
            id='test-003',
            brand=brand,
            category=category,
            title='Test',
            slug='test',
            image_url='https://test.com',
            price=Decimal('100000'),
            original_price=Decimal('150000'),
            discount_rate=Decimal('33.33'),
            seller='Test',
            deeplink='https://test.com',
            source='test',
            down_ratio='90-10',
            fill_power=800,
            hood=False
        )
        
        conditions = {
            'downRatio': '90-10',
            'fillPowerMin': 750,
            'hood': False
        }
        
        matcher = AlertMatcher()
        assert matcher.matches(product, conditions) == True
        
        conditions['fillPowerMin'] = 850
        assert matcher.matches(product, conditions) == False
