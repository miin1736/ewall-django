"""
Base Crawler Abstract Class
모든 플랫폼 크롤러의 기본 인터페이스
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class BaseCrawler(ABC):
    """크롤러 기본 클래스
    
    모든 플랫폼 크롤러는 이 클래스를 상속받아야 합니다.
    
    Attributes:
        platform_name: 플랫폼 이름 (예: 'coupang', 'naver')
        timeout: API/HTTP 요청 타임아웃 (초)
        max_retries: 실패 시 재시도 횟수
    """
    
    def __init__(self, timeout: int = 30, max_retries: int = 3):
        """
        Args:
            timeout: 요청 타임아웃 (초)
            max_retries: 재시도 횟수
        """
        self.timeout = timeout
        self.max_retries = max_retries
        self.platform_name = self._get_platform_name()
    
    @abstractmethod
    def _get_platform_name(self) -> str:
        """플랫폼 이름 반환
        
        Returns:
            플랫폼 이름 (예: 'coupang', 'naver')
        """
        pass
    
    @abstractmethod
    def search(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """상품 검색
        
        Args:
            keyword: 검색 키워드
            **kwargs: 추가 검색 옵션 (limit, category, price_range 등)
        
        Returns:
            표준화된 상품 데이터 리스트
            [
                {
                    'platform': 'coupang',
                    'product_id': '12345',
                    'title': '상품명',
                    'price': Decimal('100000'),
                    'original_price': Decimal('150000'),
                    'discount_rate': Decimal('33.33'),
                    'image_url': 'https://...',
                    'product_url': 'https://...',
                    'seller': '판매자명',
                    'rating': 4.5,
                    'review_count': 1234,
                    'delivery_info': '무료배송',
                    'in_stock': True,
                    'brand': 'BrandName',
                    'category': 'category_slug',
                    'raw_data': {...}  # 원본 데이터
                },
                ...
            ]
        """
        pass
    
    @abstractmethod
    def _fetch_raw_data(self, keyword: str, **kwargs) -> List[Dict[str, Any]]:
        """플랫폼 API/웹에서 원본 데이터 가져오기
        
        Args:
            keyword: 검색 키워드
            **kwargs: 추가 옵션
        
        Returns:
            플랫폼 원본 데이터 리스트
        """
        pass
    
    @abstractmethod
    def _parse_product(self, raw_item: Dict[str, Any]) -> Dict[str, Any]:
        """원본 데이터를 표준 형식으로 파싱
        
        Args:
            raw_item: 플랫폼 원본 데이터
        
        Returns:
            표준화된 상품 데이터
        """
        pass
    
    def _calculate_discount_rate(self, price: Decimal, original_price: Decimal) -> Decimal:
        """할인율 계산
        
        Args:
            price: 현재 가격
            original_price: 원가
        
        Returns:
            할인율 (0-100)
        """
        if original_price <= 0 or price >= original_price:
            return Decimal('0.00')
        
        discount_rate = ((original_price - price) / original_price * 100)
        return discount_rate.quantize(Decimal('0.01'))
    
    def _extract_brand(self, title: str) -> Optional[str]:
        """상품명에서 브랜드 추출
        
        Args:
            title: 상품명
        
        Returns:
            브랜드명 (추정)
        """
        # 간단한 브랜드 추출 로직
        # 실제로는 더 정교한 매칭 필요
        known_brands = [
            '노스페이스', 'The North Face',
            '파타고니아', 'Patagonia',
            '아크테릭스', "Arc'teryx",
            '밀레', 'Millet',
            '코오롱스포츠', 'Kolon Sport',
            '블랙야크', 'BlackYak',
            '네파', 'NEPA',
            '디스커버리', 'Discovery',
            '유니클로', 'Uniqlo',
        ]
        
        title_upper = title.upper()
        for brand in known_brands:
            if brand.upper() in title_upper:
                return brand
        
        # 첫 단어를 브랜드로 추정
        first_word = title.split()[0] if title.split() else None
        return first_word
    
    def _extract_category(self, title: str, category_hint: Optional[str] = None) -> str:
        """상품명에서 카테고리 추출
        
        Args:
            title: 상품명
            category_hint: 플랫폼에서 제공한 카테고리 힌트
        
        Returns:
            카테고리 slug (down, slacks, jeans 등)
        """
        title_lower = title.lower()
        
        # 카테고리 키워드 매칭 (더 구체적인 것부터 먼저 체크)
        category_keywords = {
            'jeans': ['청바지', 'jeans', '데님', 'denim'],  # 먼저 체크
            'down': ['다운', 'down', '패딩', 'padding', '점퍼', 'jumper', 'jacket'],
            'slacks': ['슬랙스', 'slacks', '정장', '팬츠', 'pants', '바지', 'trousers'],  # 나중에 체크
            'crewneck': ['크루넥', 'crewneck', '맨투맨', 'sweatshirt'],
            'long-sleeve': ['긴팔', 'long sleeve', '롱슬리브', '라운드티'],
            'coat': ['코트', 'coat', '자켓', 'jacket', '아우터'],
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
        
        return 'generic'
    
    def validate_product(self, product: Dict[str, Any]) -> bool:
        """상품 데이터 유효성 검증
        
        Args:
            product: 파싱된 상품 데이터
        
        Returns:
            유효성 여부
        """
        required_fields = [
            'platform', 'product_id', 'title', 'price',
            'image_url', 'product_url'
        ]
        
        for field in required_fields:
            if field not in product or not product[field]:
                logger.warning(f"Missing required field: {field}")
                return False
        
        # 가격 유효성
        if product['price'] <= 0:
            logger.warning(f"Invalid price: {product['price']}")
            return False
        
        return True
    
    def filter_results(
        self, 
        products: List[Dict[str, Any]], 
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        min_discount: Optional[Decimal] = None,
        in_stock_only: bool = True
    ) -> List[Dict[str, Any]]:
        """검색 결과 필터링
        
        Args:
            products: 상품 리스트
            min_price: 최소 가격
            max_price: 최대 가격
            min_discount: 최소 할인율
            in_stock_only: 재고 있는 것만
        
        Returns:
            필터링된 상품 리스트
        """
        filtered = products
        
        # 재고 필터
        if in_stock_only:
            filtered = [p for p in filtered if p.get('in_stock', True)]
        
        # 가격 필터
        if min_price is not None:
            filtered = [p for p in filtered if p['price'] >= min_price]
        
        if max_price is not None:
            filtered = [p for p in filtered if p['price'] <= max_price]
        
        # 할인율 필터
        if min_discount is not None:
            filtered = [
                p for p in filtered 
                if p.get('discount_rate', Decimal('0')) >= min_discount
            ]
        
        return filtered
    
    def __repr__(self):
        return f"<{self.__class__.__name__} platform={self.platform_name}>"
