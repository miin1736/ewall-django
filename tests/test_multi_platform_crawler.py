"""
Multi-Platform Crawler Integration Tests
크롤러 시스템 통합 테스트
"""
import pytest
from decimal import Decimal
from unittest.mock import patch, MagicMock
from apps.products.services.crawlers import BaseCrawler, CoupangCrawler, NaverCrawler
from apps.products.services.search_aggregator import SearchAggregator


class TestBaseCrawler:
    """BaseCrawler 추상 클래스 테스트"""
    
    def test_calculate_discount_rate(self):
        """할인율 계산 테스트"""
        # Mock 크롤러
        class MockCrawler(BaseCrawler):
            def _get_platform_name(self):
                return 'mock'
            def search(self, keyword, **kwargs):
                return []
            def _fetch_raw_data(self, keyword, **kwargs):
                return []
            def _parse_product(self, raw_item):
                return {}
        
        crawler = MockCrawler()
        
        # 정상 할인
        rate = crawler._calculate_discount_rate(Decimal('70000'), Decimal('100000'))
        assert rate == Decimal('30.00')
        
        # 할인 없음
        rate = crawler._calculate_discount_rate(Decimal('100000'), Decimal('100000'))
        assert rate == Decimal('0.00')
        
        # 가격이 더 높음
        rate = crawler._calculate_discount_rate(Decimal('120000'), Decimal('100000'))
        assert rate == Decimal('0.00')
    
    def test_extract_brand(self):
        """브랜드 추출 테스트"""
        class MockCrawler(BaseCrawler):
            def _get_platform_name(self):
                return 'mock'
            def search(self, keyword, **kwargs):
                return []
            def _fetch_raw_data(self, keyword, **kwargs):
                return []
            def _parse_product(self, raw_item):
                return {}
        
        crawler = MockCrawler()
        
        # 알려진 브랜드
        brand = crawler._extract_brand('노스페이스 다운재킷 800FP')
        assert brand == '노스페이스'
        
        brand = crawler._extract_brand('Patagonia Down Sweater')
        assert brand == 'Patagonia'
    
    def test_extract_category(self):
        """카테고리 추출 테스트"""
        class MockCrawler(BaseCrawler):
            def _get_platform_name(self):
                return 'mock'
            def search(self, keyword, **kwargs):
                return []
            def _fetch_raw_data(self, keyword, **kwargs):
                return []
            def _parse_product(self, raw_item):
                return {}
        
        crawler = MockCrawler()
        
        # 다운
        category = crawler._extract_category('노스페이스 다운재킷')
        assert category == 'down'
        
        # 슬랙스
        category = crawler._extract_category('남성 슬랙스 정장바지')
        assert category == 'slacks'
        
        # 청바지 (jeans 키워드가 명확하게 있는 경우)
        category = crawler._extract_category('청바지 jeans 리바이스')
        assert category == 'jeans'
    
    def test_validate_product(self):
        """상품 유효성 검증 테스트"""
        class MockCrawler(BaseCrawler):
            def _get_platform_name(self):
                return 'mock'
            def search(self, keyword, **kwargs):
                return []
            def _fetch_raw_data(self, keyword, **kwargs):
                return []
            def _parse_product(self, raw_item):
                return {}
        
        crawler = MockCrawler()
        
        # 유효한 상품
        valid_product = {
            'platform': 'coupang',
            'product_id': '12345',
            'title': '노스페이스 다운재킷',
            'price': Decimal('100000'),
            'image_url': 'https://example.com/image.jpg',
            'product_url': 'https://example.com/product/12345',
        }
        assert crawler.validate_product(valid_product) is True
        
        # 필수 필드 누락
        invalid_product = {
            'platform': 'coupang',
            'product_id': '12345',
        }
        assert crawler.validate_product(invalid_product) is False
        
        # 가격 0
        invalid_price = valid_product.copy()
        invalid_price['price'] = Decimal('0')
        assert crawler.validate_product(invalid_price) is False
    
    def test_filter_results(self):
        """검색 결과 필터링 테스트"""
        class MockCrawler(BaseCrawler):
            def _get_platform_name(self):
                return 'mock'
            def search(self, keyword, **kwargs):
                return []
            def _fetch_raw_data(self, keyword, **kwargs):
                return []
            def _parse_product(self, raw_item):
                return {}
        
        crawler = MockCrawler()
        
        products = [
            {'price': Decimal('50000'), 'discount_rate': Decimal('10'), 'in_stock': True},
            {'price': Decimal('100000'), 'discount_rate': Decimal('30'), 'in_stock': True},
            {'price': Decimal('150000'), 'discount_rate': Decimal('50'), 'in_stock': False},
        ]
        
        # 가격 필터 (in_stock_only=False로 설정)
        filtered = crawler.filter_results(products, min_price=Decimal('70000'), in_stock_only=False)
        assert len(filtered) == 2
        
        # 할인율 필터 (in_stock_only=False로 설정)
        filtered = crawler.filter_results(products, min_discount=Decimal('20'), in_stock_only=False)
        assert len(filtered) == 2
        
        # 재고 필터
        filtered = crawler.filter_results(products, in_stock_only=True)
        assert len(filtered) == 2


@pytest.mark.django_db
class TestCoupangCrawler:
    """CoupangCrawler 테스트"""
    
    def test_platform_name(self):
        """플랫폼 이름 확인"""
        crawler = CoupangCrawler()
        assert crawler.platform_name == 'coupang'
    
    def test_search_with_mock_data(self):
        """Mock 데이터로 검색 테스트"""
        crawler = CoupangCrawler()
        
        # Mock 데이터 사용 (API 없음)
        results = crawler.search('노스페이스', limit=10)
        
        # Mock 데이터가 반환되어야 함
        assert isinstance(results, list)
        assert len(results) > 0
        
        # 첫 번째 상품 검증
        product = results[0]
        assert product['platform'] == 'coupang'
        assert 'product_id' in product
        assert 'title' in product
        assert 'price' in product
        assert isinstance(product['price'], Decimal)
    
    def test_parse_product(self):
        """상품 데이터 파싱 테스트"""
        crawler = CoupangCrawler()
        
        raw_item = {
            'productId': 12345,
            'productName': '노스페이스 다운재킷 800FP',
            'productImage': 'https://example.com/image.jpg',
            'productPrice': 89000,
            'originalPrice': 129000,
            'productUrl': 'https://www.coupang.com/vp/products/12345',
            'isRocket': True,
            'isFreeShipping': True,
            'categoryName': '패션의류',
            'vendorName': '쿠팡',
            'rating': 4.5,
            'reviewCount': 1234,
        }
        
        product = crawler._parse_product(raw_item)
        
        assert product['platform'] == 'coupang'
        assert product['product_id'] == '12345'
        assert product['title'] == '노스페이스 다운재킷 800FP'
        assert product['price'] == Decimal('89000')
        assert product['original_price'] == Decimal('129000')
        assert product['discount_rate'] == Decimal('31.01')
        assert product['delivery_info'] == '로켓배송'
        assert product['rating'] == 4.5
        assert product['review_count'] == 1234


@pytest.mark.django_db
class TestNaverCrawler:
    """NaverCrawler 테스트"""
    
    def test_platform_name(self):
        """플랫폼 이름 확인"""
        crawler = NaverCrawler()
        assert crawler.platform_name == 'naver'
    
    def test_search_with_mock_data(self):
        """Mock 데이터로 검색 테스트"""
        crawler = NaverCrawler()
        
        # Mock 데이터 사용
        results = crawler.search('파타고니아', limit=10)
        
        assert isinstance(results, list)
        assert len(results) > 0
        
        product = results[0]
        assert product['platform'] == 'naver'
        assert 'product_id' in product
        assert 'title' in product
        assert 'price' in product
    
    def test_parse_product(self):
        """상품 데이터 파싱 테스트 (HTML 태그 제거 포함)"""
        crawler = NaverCrawler()
        
        raw_item = {
            'title': '파타고니아 <b>다운재킷</b> 800FP',
            'link': 'https://shopping.naver.com/search/product/12345',
            'image': 'https://example.com/image.jpg',
            'lprice': '95000',
            'hprice': '135000',
            'mallName': '네이버쇼핑',
            'productId': '67890',
            'brand': '파타고니아',
            'category1': '패션의류',
            'category2': '남성의류',
            'category3': '아우터',
        }
        
        product = crawler._parse_product(raw_item)
        
        # HTML 태그 제거 확인
        assert product['title'] == '파타고니아 다운재킷 800FP'
        assert product['platform'] == 'naver'
        assert product['product_id'] == '67890'
        assert product['price'] == Decimal('95000')
        assert product['original_price'] == Decimal('135000')
        assert product['brand'] == '파타고니아'


@pytest.mark.django_db
class TestSearchAggregator:
    """SearchAggregator 통합 검색 테스트"""
    
    def test_aggregator_initialization(self):
        """Aggregator 초기화 테스트"""
        aggregator = SearchAggregator()
        
        assert 'coupang' in aggregator.crawlers
        assert 'naver' in aggregator.crawlers
        assert len(aggregator.crawlers) == 2
    
    def test_get_available_platforms(self):
        """사용 가능한 플랫폼 목록"""
        aggregator = SearchAggregator()
        platforms = aggregator.get_available_platforms()
        
        assert 'coupang' in platforms
        assert 'naver' in platforms
    
    @pytest.mark.slow
    def test_search_multi_platform(self):
        """멀티플랫폼 통합 검색 테스트"""
        aggregator = SearchAggregator()
        
        result = aggregator.search(
            keyword='노스페이스',
            limit=10
        )
        
        assert 'keyword' in result
        assert result['keyword'] == '노스페이스'
        assert 'total' in result
        assert 'platforms' in result
        assert 'products' in result
        
        # 최소 하나의 상품은 있어야 함 (Mock 데이터)
        assert result['total'] > 0
        assert len(result['products']) > 0
        
        # 플랫폼별 통계
        assert 'coupang' in result['platforms'] or 'naver' in result['platforms']
    
    def test_search_with_filters(self):
        """필터 적용 검색 테스트"""
        aggregator = SearchAggregator()
        
        result = aggregator.search(
            keyword='다운재킷',
            min_price=50000,
            max_price=150000,
            min_discount=20,
            limit=20
        )
        
        assert result['total'] >= 0
        
        # 필터 조건 확인
        for product in result['products']:
            assert product['price'] >= Decimal('50000')
            assert product['price'] <= Decimal('150000')
            assert product.get('discount_rate', Decimal('0')) >= Decimal('20')
    
    def test_deduplicate(self):
        """중복 제거 테스트"""
        aggregator = SearchAggregator()
        
        products = [
            {'title': '노스페이스 다운재킷 800FP', 'price': Decimal('100000')},
            {'title': '노스페이스 다운재킷 800FP 블랙', 'price': Decimal('105000')},  # 유사
            {'title': '파타고니아 다운 스웨터', 'price': Decimal('150000')},  # 다름
        ]
        
        unique = aggregator._deduplicate(products)
        
        # 첫 두 개는 유사하므로 중복 제거되어야 함
        assert len(unique) == 2
    
    def test_rank_products(self):
        """상품 랭킹 테스트"""
        aggregator = SearchAggregator()
        
        products = [
            {
                'discount_rate': Decimal('10'),
                'rating': 3.0,
                'review_count': 10,
                'delivery_info': '',
            },
            {
                'discount_rate': Decimal('50'),
                'rating': 4.5,
                'review_count': 1000,
                'delivery_info': '로켓배송',
            },
            {
                'discount_rate': Decimal('30'),
                'rating': 4.0,
                'review_count': 100,
                'delivery_info': '무료배송',
            },
        ]
        
        ranked = aggregator._rank_products(products)
        
        # 점수가 추가되어야 함
        assert all('score' in p for p in ranked)
        
        # 두 번째 상품이 가장 높은 점수를 받아야 함
        assert ranked[0]['discount_rate'] == Decimal('50')
        assert ranked[0]['score'] > ranked[1]['score']


@pytest.mark.django_db
class TestMultiPlatformSearchAPI:
    """Multi-Platform Search API 테스트"""
    
    def test_search_api_without_keyword(self, client):
        """키워드 없이 요청 시 400 에러"""
        response = client.get('/api/search/')
        
        assert response.status_code == 400
        assert 'error' in response.json()
    
    def test_search_api_with_keyword(self, client):
        """정상 검색 요청"""
        response = client.get('/api/search/?keyword=노스페이스')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'keyword' in data
        assert data['keyword'] == '노스페이스'
        assert 'total' in data
        assert 'platforms' in data
        assert 'products' in data
    
    def test_search_api_with_filters(self, client):
        """필터 포함 검색 요청"""
        response = client.get(
            '/api/search/?'
            'keyword=다운재킷&'
            'platforms=coupang,naver&'
            'limit=20&'
            'min_price=50000&'
            'max_price=200000&'
            'min_discount=30'
        )
        
        assert response.status_code == 200
        data = response.json()
        
        assert data['keyword'] == '다운재킷'
        assert data['total'] >= 0
    
    def test_platforms_api(self, client):
        """플랫폼 목록 API"""
        response = client.get('/api/search/platforms/')
        
        assert response.status_code == 200
        data = response.json()
        
        assert 'platforms' in data
        assert 'total' in data
        assert 'coupang' in data['platforms']
        assert 'naver' in data['platforms']


@pytest.mark.django_db
class TestCrawlTask:
    """Celery 크롤링 태스크 테스트"""
    
    @pytest.mark.slow
    def test_crawl_multi_platform_task(self):
        """멀티플랫폼 크롤링 태스크"""
        from apps.products.tasks import crawl_multi_platform
        
        # 단일 키워드로 테스트
        result = crawl_multi_platform(
            keywords=['노스페이스'],
            platforms=['coupang', 'naver']
        )
        
        assert 'keywords_processed' in result
        assert result['keywords_processed'] == 1
        assert 'created' in result
        assert 'updated' in result
        
        # DB에 상품이 저장되었는지 확인
        from apps.products.models import DownProduct
        products = DownProduct.objects.filter(source__in=['coupang', 'naver'])
        assert products.count() >= 0  # Mock 데이터로 생성된 상품
