"""
Naver Shopping Crawler
네이버 쇼핑 검색 크롤러
"""
import logging
import requests
from typing import List, Dict, Any, Optional
from decimal import Decimal
from django.conf import settings
from .base import BaseCrawler

logger = logging.getLogger(__name__)


class NaverCrawler(BaseCrawler):
    """네이버 쇼핑 검색 API 크롤러
    
    네이버 쇼핑 검색 API 사용
    API 문서: https://developers.naver.com/docs/serviceapi/search/shopping/shopping.md
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        super().__init__(timeout, max_retries)
        self.client_id = settings.NAVER_CLIENT_ID
        self.client_secret = settings.NAVER_CLIENT_SECRET
        
        if not self.client_id or not self.client_secret:
            logger.warning("Naver API credentials not configured")
    
    def _get_platform_name(self) -> str:
        return 'naver'
    
    def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """네이버 쇼핑에서 상품 검색
        
        Args:
            keyword: 검색 키워드
            **kwargs:
                - limit: 최대 결과 수 (기본 100, 최대 100)
                - start: 검색 시작 위치 (기본 1)
                - sort: 정렬 (sim: 정확도순, date: 날짜순, asc: 가격오름차순, dsc: 가격내림차순)
        
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
            
            logger.info(f"Naver: Found {len(products)} valid products for '{keyword}'")
            return products
            
        except Exception as e:
            logger.error(f"Naver search failed: {e}")
            return []
    
    def _fetch_raw_data(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """네이버 쇼핑 API 호출
        
        Endpoint: https://openapi.naver.com/v1/search/shop.json
        """
        try:
            # API가 없으면 Mock 데이터 반환
            if not self.client_id or not self.client_secret:
                logger.warning("Using mock data for Naver (no API credentials)")
                return self._get_mock_data(keyword)
            
            # API 호출
            url = "https://openapi.naver.com/v1/search/shop.json"
            
            limit = min(kwargs.get('limit', 100), 100)
            start = kwargs.get('start', 1)
            sort = kwargs.get('sort', 'sim')  # sim, date, asc, dsc
            
            headers = {
                'X-Naver-Client-Id': self.client_id,
                'X-Naver-Client-Secret': self.client_secret,
            }
            
            params = {
                'query': keyword,
                'display': limit,
                'start': start,
                'sort': sort,
            }
            
            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=self.timeout
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            logger.info(f"Naver API: Fetched {len(items)} products")
            return items
            
        except requests.RequestException as e:
            logger.error(f"Naver API request failed: {e}")
            # Fallback to mock data
            return self._get_mock_data(keyword)
    
    def _parse_product(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """네이버 쇼핑 원본 데이터 파싱
        
        네이버 API 응답 예시:
        {
            "title": "노스페이스 <b>다운재킷</b>",
            "link": "https://shopping.naver.com/...",
            "image": "https://...",
            "lprice": "89000",
            "hprice": "129000",
            "mallName": "네이버쇼핑",
            "productId": "12345678",
            "productType": "1",
            "brand": "노스페이스",
            "maker": "...",
            "category1": "패션의류",
            "category2": "남성의류",
            "category3": "아우터"
        }
        """
        # HTML 태그 제거 (<b>, </b> 등)
        import re
        title = raw_item.get('title', '')
        title = re.sub(r'<[^>]+>', '', title)  # HTML 태그 제거
        
        # 가격 파싱 (lprice: 최저가, hprice: 최고가)
        lprice = raw_item.get('lprice', '0')
        hprice = raw_item.get('hprice', lprice)
        
        # 문자열을 Decimal로 변환
        price = Decimal(str(lprice))
        original_price = Decimal(str(hprice)) if hprice != lprice else price
        
        # 할인율 계산
        discount_rate = self._calculate_discount_rate(price, original_price)
        
        # 브랜드 (API에서 제공하거나 제목에서 추출)
        brand = raw_item.get('brand') or self._extract_brand(title)
        
        # 카테고리
        category_hint = raw_item.get('category3') or raw_item.get('category2')
        category = self._extract_category(title, category_hint=category_hint)
        
        # 표준 형식으로 변환
        product = {
            'platform': self.platform_name,
            'product_id': str(raw_item.get('productId', '')),
            'title': title,
            'price': price,
            'original_price': original_price,
            'discount_rate': discount_rate,
            'image_url': raw_item.get('image', ''),
            'product_url': raw_item.get('link', ''),
            'seller': raw_item.get('mallName', '네이버쇼핑'),
            'rating': 0.0,  # 네이버 API는 평점 미제공
            'review_count': 0,  # 네이버 API는 리뷰 수 미제공
            'delivery_info': '',  # 배송 정보 미제공
            'in_stock': True,  # 검색 결과는 재고 있음으로 가정
            'brand': brand,
            'category': category,
            'raw_data': raw_item,
        }
        
        return product
    
    def _get_mock_data(self, keyword: str) -> List[Dict[str, Any]]:
        """Mock 데이터 생성 (개발/테스트용)"""
        import random
        
        mock_products = []
        brands = ['노스페이스', '파타고니아', '아크테릭스', '밀레']
        categories = ['다운재킷', '슬랙스', '청바지', '코트']
        
        num_products = random.randint(3, 5)
        
        for i in range(num_products):
            brand = random.choice(brands)
            category = random.choice(categories)
            
            lprice = random.randint(50000, 200000)
            hprice = int(lprice * random.uniform(1.1, 1.5))
            
            mock_products.append({
                'title': f'{brand} <b>{category}</b> {keyword}',
                'link': f'https://shopping.naver.com/search/product/{i+1}',
                'image': f'https://via.placeholder.com/300x300?text={brand}',
                'lprice': str(lprice),
                'hprice': str(hprice),
                'mallName': '네이버쇼핑',
                'productId': f'naver-mock-{i+1}',
                'productType': '1',
                'brand': brand,
                'category1': '패션의류',
                'category2': '남성의류',
                'category3': category,
            })
        
        logger.info(f"Generated {len(mock_products)} mock products for '{keyword}'")
        return mock_products
