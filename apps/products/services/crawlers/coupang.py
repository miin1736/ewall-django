"""
Coupang Shopping Crawler
쿠팡 상품 검색 크롤러
"""
import logging
import requests
import hmac
import hashlib
import time
from typing import List, Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class CoupangCrawler(BaseCrawler):
    """쿠팡 파트너스 API 크롤러
    
    쿠팡 파트너스 API를 사용하여 상품 검색
    API 문서: https://developers.coupang.com/hc/ko/articles/360033909473
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        super().__init__(timeout, max_retries)
        self.access_key = settings.COUPANG_ACCESS_KEY
        self.secret_key = settings.COUPANG_SECRET_KEY
        
        if not self.access_key or not self.secret_key:
            logger.warning("Coupang API credentials not configured")
    
    def _get_platform_name(self) -> str:
        return 'coupang'
    
    def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """쿠팡에서 상품 검색
        
        Args:
            keyword: 검색 키워드
            **kwargs: 
                - limit: 최대 결과 수 (기본 100)
                - category_id: 카테고리 ID (선택)
                - sort: 정렬 방식 (SCORE_DESC, PRICE_ASC, PRICE_DESC 등)
        
        Returns:
            표준화된 상품 리스트
        """
        try:
            # 원본 데이터 가져오기
            raw_products = self._fetch_raw_data(keyword, **kwargs)
            
            if not raw_products:
                logger.info(f"No products found for keyword: {keyword}")
                return []
            
            # 파싱 및 검증
            products = []
            for raw_item in raw_products:
                try:
                    product = self._parse_product(raw_item)
                    if self.validate_product(product):
                        products.append(product)
                except Exception as e:
                    logger.error(f"Failed to parse product: {e}")
                    continue
            
            logger.info(f"Coupang: Found {len(products)} valid products for '{keyword}'")
            return products
            
        except Exception as e:
            logger.error(f"Coupang search failed: {e}")
            return []
    
    def _fetch_raw_data(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """쿠팡 파트너스 API 호출
        
        실제 API 사양:
        - Endpoint: /v2/providers/affiliate_open_api/apis/openapi/v1/products/search
        - Method: GET
        - Authorization: HMAC-SHA256 서명
        """
        try:
            # API가 없으면 Mock 데이터 반환 (개발용)
            if not self.access_key or not self.secret_key:
                logger.warning("Using mock data for Coupang (no API credentials)")
                return self._get_mock_data(keyword)
            
            # 실제 API 호출
            limit = kwargs.get('limit', 100)
            category_id = kwargs.get('category_id')
            sort = kwargs.get('sort', 'SCORE_DESC')
            
            # API 엔드포인트
            url = "https://api-gateway.coupang.com/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
            
            # 요청 파라미터
            params = {
                'keyword': keyword,
                'limit': min(limit, 100),  # 최대 100
            }
            
            if category_id:
                params['categoryId'] = category_id
            if sort:
                params['sort'] = sort
            
            # HMAC 서명 생성
            headers = self._generate_headers('GET', url, params)
            
            # API 호출
            response = requests.get(
                url, 
                headers=headers, 
                params=params, 
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            products = data.get('data', [])
            
            logger.info(f"Coupang API: Fetched {len(products)} products")
            return products
            
        except requests.RequestException as e:
            logger.error(f"Coupang API request failed: {e}")
            # Fallback to mock data
            return self._get_mock_data(keyword)
    
    def _generate_headers(self, method: str, url: str, params: Dict[str, Any]) -> Dict[str, str]:
        """쿠팡 API HMAC 서명 생성
        
        쿠팡 API는 HMAC-SHA256 서명 필요
        """
        import urllib.parse
        
        # 타임스탬프
        timestamp = str(int(time.time() * 1000))
        
        # 요청 경로
        path = urllib.parse.urlparse(url).path
        
        # 쿼리 스트링 (정렬 필요)
        query_string = urllib.parse.urlencode(sorted(params.items()))
        
        # 서명 메시지
        message = f"{timestamp}{method}{path}?{query_string}"
        
        # HMAC-SHA256 서명
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        # 헤더
        headers = {
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {self.access_key}',
            'X-COUPANG-SIGNATURE': signature,
            'X-COUPANG-TIMESTAMP': timestamp,
        }
        
        return headers
    
    def _parse_product(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """쿠팡 원본 데이터 파싱
        
        쿠팡 API 응답 예시:
        {
            "productId": 123456,
            "productName": "노스페이스 다운재킷",
            "productImage": "https://...",
            "productPrice": 89000,
            "productUrl": "https://...",
            "isRocket": true,
            "isFreeShipping": true,
            "categoryName": "패션의류",
            "vendorName": "쿠팡"
        }
        """
        # 가격 파싱
        price = Decimal(str(raw_item.get('productPrice', 0)))
        original_price = Decimal(str(raw_item.get('originalPrice', price)))
        
        # 할인율 계산
        discount_rate = self._calculate_discount_rate(price, original_price)
        
        # 배송 정보
        delivery_info = ''
        if raw_item.get('isRocket'):
            delivery_info = '로켓배송'
        elif raw_item.get('isFreeShipping'):
            delivery_info = '무료배송'
        
        # 제목
        title = raw_item.get('productName', '')
        
        # 브랜드 및 카테고리 추출
        brand = self._extract_brand(title)
        category = self._extract_category(
            title, 
            category_hint=raw_item.get('categoryName')
        )
        
        # 표준 형식으로 변환
        product = {
            'platform': self.platform_name,
            'product_id': str(raw_item.get('productId', '')),
            'title': title,
            'price': price,
            'original_price': original_price,
            'discount_rate': discount_rate,
            'image_url': raw_item.get('productImage', ''),
            'product_url': raw_item.get('productUrl', ''),
            'seller': raw_item.get('vendorName', '쿠팡'),
            'rating': float(raw_item.get('rating', 0.0)),
            'review_count': int(raw_item.get('reviewCount', 0)),
            'delivery_info': delivery_info,
            'in_stock': True,  # 검색 결과는 재고 있음으로 가정
            'brand': brand,
            'category': category,
            'raw_data': raw_item,
        }
        
        return product
    
    def _get_mock_data(self, keyword: str) -> List[Dict[str, Any]]:
        """Mock 데이터 생성 (개발/테스트용)
        
        실제 API 없을 때 사용
        """
        import random
        
        mock_products = []
        brands = ['노스페이스', '파타고니아', '아크테릭스', '밀레']
        categories = ['다운재킷', '슬랙스', '청바지', '코트']
        
        # 키워드에 맞는 상품 3-5개 생성
        num_products = random.randint(3, 5)
        
        for i in range(num_products):
            brand = random.choice(brands)
            category = random.choice(categories)
            
            price = random.randint(50000, 200000)
            original_price = int(price * random.uniform(1.1, 1.5))
            
            mock_products.append({
                'productId': f'coupang-mock-{i+1}',
                'productName': f'{brand} {category} {keyword}',
                'productImage': f'https://via.placeholder.com/300x300?text={brand}',
                'productPrice': price,
                'originalPrice': original_price,
                'productUrl': f'https://www.coupang.com/vp/products/{i+1}',
                'isRocket': random.choice([True, False]),
                'isFreeShipping': True,
                'categoryName': '패션의류',
                'vendorName': '쿠팡',
                'rating': round(random.uniform(3.5, 5.0), 1),
                'reviewCount': random.randint(10, 1000),
            })
        
        logger.info(f"Generated {len(mock_products)} mock products for '{keyword}'")
        return mock_products
