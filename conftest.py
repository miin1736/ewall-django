import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from apps.core.models import Brand, Category
from apps.products.models import DownProduct, CoatProduct, JeansProduct


User = get_user_model()


@pytest.fixture
def api_client():
    """API 테스트용 클라이언트"""
    return APIClient()


@pytest.fixture
def authenticated_client(db, api_client):
    """인증된 API 클라이언트"""
    user = User.objects.create_user(
        username='testuser',
        email='testuser@example.com',
        password='testpass123'
    )
    api_client.force_authenticate(user=user)
    return api_client


@pytest.fixture
def admin_client(db, api_client):
    """관리자 권한 API 클라이언트"""
    admin = User.objects.create_superuser(
        username='admin',
        email='admin@test.com',
        password='admin123'
    )
    api_client.force_authenticate(user=admin)
    return api_client


@pytest.fixture
def sample_user(db):
    """테스트용 일반 사용자"""
    return User.objects.create_user(
        username='sampleuser',
        email='sample@example.com',
        password='pass123'
    )


@pytest.fixture
def sample_brand(db):
    """테스트용 브랜드"""
    return Brand.objects.create(name='Test Brand')


@pytest.fixture
def sample_category(db):
    """테스트용 카테고리"""
    return Category.objects.create(
        name='Test Category',
        description='Test Description'
    )


@pytest.fixture
def sample_down_product(db, sample_brand, sample_category):
    """테스트용 다운 상품"""
    from decimal import Decimal
    return DownProduct.objects.create(
        id='DOWN-TEST-001',
        title='Test Down Jacket',
        slug='test-down-jacket',
        brand=sample_brand,
        category=sample_category,
        price=Decimal('199.99'),
        original_price=Decimal('299.99'),
        discount_rate=Decimal('33.33'),
        image_url='https://example.com/test.jpg',
        deeplink='https://example.com/product/test',
        seller='TestSeller',
        source='test',
        in_stock=True,
        fill_power=800,
        down_type='goose',
        down_ratio='90/10'
    )


@pytest.fixture
def sample_coat_product(db, sample_brand, sample_category):
    """테스트용 코트 상품"""
    from decimal import Decimal
    return CoatProduct.objects.create(
        id='COAT-TEST-001',
        title='Test Coat',
        slug='test-coat',
        brand=sample_brand,
        category=sample_category,
        price=Decimal('149.99'),
        original_price=Decimal('199.99'),
        discount_rate=Decimal('25.00'),
        image_url='https://example.com/test-coat.jpg',
        deeplink='https://example.com/product/test-coat',
        seller='TestSeller',
        source='test',
        in_stock=True,
        length='long',
        shell='wool'
    )


@pytest.fixture
def sample_jeans_product(db, sample_brand, sample_category):
    """테스트용 청바지 상품"""
    from decimal import Decimal
    return JeansProduct.objects.create(
        id='JEANS-TEST-001',
        title='Test Jeans',
        slug='test-jeans',
        brand=sample_brand,
        category=sample_category,
        price=Decimal('59.99'),
        original_price=Decimal('89.99'),
        discount_rate=Decimal('33.33'),
        image_url='https://example.com/test-jeans.jpg',
        deeplink='https://example.com/product/test-jeans',
        seller='TestSeller',
        source='test',
        in_stock=True,
        wash='dark',
        cut='slim'
    )


@pytest.fixture
def sample_alert(db, sample_down_product):
    """테스트용 알림"""
    from decimal import Decimal
    from apps.alerts.models import Alert
    
    return Alert.objects.create(
        user_email='test@example.com',
        target_price=Decimal('150.00'),
        product_code=sample_down_product.id,
        product_name=sample_down_product.title,
        current_price=sample_down_product.price,
        is_active=True
    )


@pytest.fixture
def sample_click(db, sample_down_product):
    """테스트용 클릭 데이터"""
    from django.utils import timezone
    from apps.analytics.models import Click
    
    return Click.objects.create(
        product_code=sample_down_product.id,
        user_identifier='test_user_1',
        clicked_at=timezone.now()
    )
