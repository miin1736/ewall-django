"""
Product Normalizer Service
제휴사 데이터를 표준 형식으로 정규화
"""
from typing import Dict, Any
from decimal import Decimal
from django.utils.text import slugify
from apps.products.services.attribute_extractor import AttributeExtractor


class ProductNormalizer:
    """제휴사 데이터 정규화"""
    
    @staticmethod
    def normalize(raw_data: Dict[str, Any], source: str = 'coupang') -> Dict[str, Any]:
        """제휴사 데이터를 표준 형식으로 변환
        
        Args:
            raw_data: 제휴사 원본 데이터
            source: 제휴사명 (coupang, linkprice 등)
        
        Returns:
            정규화된 상품 데이터
        """
        if source == 'coupang':
            return ProductNormalizer._normalize_coupang(raw_data)
        elif source == 'linkprice':
            return ProductNormalizer._normalize_linkprice(raw_data)
        else:
            raise ValueError(f"Unsupported source: {source}")
    
    @staticmethod
    def _normalize_coupang(data: Dict[str, Any]) -> Dict[str, Any]:
        """쿠팡 파트너스 데이터 정규화
        
        쿠팡 API 예상 필드:
        - productId, productName, productImage
        - productPrice, originalPrice
        - categoryName, vendorName
        - productUrl
        """
        # 가격 계산
        price = Decimal(str(data.get('productPrice', 0)))
        original_price = Decimal(str(data.get('originalPrice', price)))
        
        if original_price > 0:
            discount_rate = ((original_price - price) / original_price * 100).quantize(Decimal('0.01'))
        else:
            discount_rate = Decimal('0.00')
        
        # 제목 + 설명 텍스트
        text = f"{data.get('productName', '')} {data.get('description', '')}"
        
        # 카테고리 매핑 (임시 - 실제로는 DB 조회 필요)
        category_slug = ProductNormalizer._map_category(data.get('categoryName', ''))
        
        # 속성 추출
        attributes = AttributeExtractor.extract(text, category_slug)
        
        # 정규화된 데이터
        normalized = {
            'id': f"coupang-{data.get('productId')}",
            'title': data.get('productName', ''),
            'slug': slugify(data.get('productName', ''), allow_unicode=True),
            'image_url': data.get('productImage', ''),
            'price': price,
            'original_price': original_price,
            'discount_rate': discount_rate,
            'currency': 'KRW',
            'seller': data.get('vendorName', 'Coupang'),
            'deeplink': data.get('productUrl', ''),
            'in_stock': data.get('isRocket', True),  # 로켓배송 = 재고 있음으로 가정
            'score': 0.0,  # 초기 점수
            'source': 'coupang',
            'category_slug': category_slug,
            **attributes  # 추출된 속성 병합
        }
        
        return normalized
    
    @staticmethod
    def _normalize_linkprice(data: Dict[str, Any]) -> Dict[str, Any]:
        """링크프라이스 데이터 정규화"""
        # 링크프라이스 API 구조에 맞게 구현
        # 여기서는 예시만 제공
        
        price = Decimal(str(data.get('price', 0)))
        original_price = Decimal(str(data.get('original_price', price)))
        
        if original_price > 0:
            discount_rate = ((original_price - price) / original_price * 100).quantize(Decimal('0.01'))
        else:
            discount_rate = Decimal('0.00')
        
        text = f"{data.get('name', '')} {data.get('description', '')}"
        category_slug = ProductNormalizer._map_category(data.get('category', ''))
        attributes = AttributeExtractor.extract(text, category_slug)
        
        normalized = {
            'id': f"linkprice-{data.get('id')}",
            'title': data.get('name', ''),
            'slug': slugify(data.get('name', ''), allow_unicode=True),
            'image_url': data.get('image', ''),
            'price': price,
            'original_price': original_price,
            'discount_rate': discount_rate,
            'currency': 'KRW',
            'seller': data.get('merchant', 'LinkPrice'),
            'deeplink': data.get('url', ''),
            'in_stock': True,
            'score': 0.0,
            'source': 'linkprice',
            'category_slug': category_slug,
            **attributes
        }
        
        return normalized
    
    @staticmethod
    def _map_category(category_name: str) -> str:
        """카테고리명을 slug로 매핑
        
        실제로는 DB에서 Category 모델을 조회하는 것이 좋습니다.
        """
        category_map = {
            '다운': 'down',
            '다운재킷': 'down',
            '패딩': 'down',
            '슬랙스': 'slacks',
            '바지': 'slacks',
            '청바지': 'jeans',
            '데님': 'jeans',
            '크루넥': 'crewneck',
            '맨투맨': 'crewneck',
            '긴팔': 'long-sleeve',
            '롱슬리브': 'long-sleeve',
            '코트': 'coat',
            '자켓': 'coat',
        }
        
        for key, value in category_map.items():
            if key in category_name:
                return value
        
        return 'generic'
