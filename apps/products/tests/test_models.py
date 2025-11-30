import pytest
from decimal import Decimal
from apps.products.models import DownProduct, CoatProduct, JeansProduct


@pytest.mark.unit
class TestDownProductModel:
    """DownProduct 모델 단위 테스트"""
    
    def test_create_down_product(self, sample_down_product):
        """다운 상품 생성 테스트"""
        assert sample_down_product.id == 'DOWN-TEST-001'
        assert sample_down_product.title == 'Test Down Jacket'
        assert sample_down_product.fill_power == 800
        assert sample_down_product.down_type == 'goose'
    
    def test_down_product_price_calculation(self, sample_down_product):
        """다운 상품 가격 계산 테스트"""
        assert sample_down_product.original_price == Decimal('299.99')
        assert sample_down_product.price == Decimal('199.99')
        assert sample_down_product.discount_rate == Decimal('33.33')
    
    def test_down_product_stock_status(self, sample_down_product):
        """다운 상품 재고 상태 테스트"""
        assert sample_down_product.in_stock is True
    
    def test_down_product_str_representation(self, sample_down_product):
        """다운 상품 문자열 표현 테스트"""
        assert str(sample_down_product) == sample_down_product.title


@pytest.mark.unit
class TestCoatProductModel:
    """CoatProduct 모델 단위 테스트"""
    
    def test_create_coat_product(self, sample_coat_product):
        """코트 상품 생성 테스트"""
        assert sample_coat_product.id == 'COAT-TEST-001'
        assert sample_coat_product.title == 'Test Coat'
        assert sample_coat_product.length == 'long'
        assert sample_coat_product.shell == 'wool'
    
    def test_coat_product_discount(self, sample_coat_product):
        """코트 상품 할인 테스트"""
        assert sample_coat_product.original_price > sample_coat_product.price
        assert sample_coat_product.discount_rate == Decimal('25.00')


@pytest.mark.unit
class TestJeansProductModel:
    """JeansProduct 모델 단위 테스트"""
    
    def test_create_jeans_product(self, sample_jeans_product):
        """청바지 상품 생성 테스트"""
        assert sample_jeans_product.id == 'JEANS-TEST-001'
        assert sample_jeans_product.title == 'Test Jeans'
        assert sample_jeans_product.wash == 'dark'
        assert sample_jeans_product.cut == 'slim'
    
    def test_jeans_product_active_status(self, sample_jeans_product):
        """청바지 상품 재고 상태 테스트"""
        assert sample_jeans_product.in_stock is True
        
        # 품절 처리 테스트
        sample_jeans_product.in_stock = False
        sample_jeans_product.save()
        assert sample_jeans_product.in_stock is False
