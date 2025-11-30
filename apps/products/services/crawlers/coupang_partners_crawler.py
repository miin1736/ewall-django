"""
쿠팡 파트너스 API 크롤러
공식 제휴 API로 실제 상품 데이터 수집
"""
import requests
import hmac
import hashlib
import logging
from typing import List, Dict, Optional
from datetime import datetime
from django.conf import settings

logger = logging.getLogger(__name__)


class CoupangPartnersCrawler:
    """쿠팡 파트너스 API 크롤러"""
    
    def __init__(self):
        self.access_key = getattr(settings, 'COUPANG_ACCESS_KEY', '')
        self.secret_key = getattr(settings, 'COUPANG_SECRET_KEY', '')
        self.base_url = "https://api-gateway.coupang.com"
        
        if not self.access_key or not self.secret_key:
            logger.warning("Coupang Partners API credentials not configured")
    
    def search(self, keyword: str, limit: int = 100) -> List[Dict]:
        """쿠팡 상품 검색
        
        Args:
            keyword: 검색 키워드
            limit: 최대 결과 수
        
        Returns:
            정규화된 상품 리스트
        """
        if not self.access_key or not self.secret_key:
            logger.error("Coupang API credentials missing")
            return []
        
        try:
            # 상품 검색 API 엔드포인트
            path = "/v2/providers/affiliate_open_api/apis/openapi/v1/products/search"
            url = self.base_url + path
            
            # 요청 파라미터
            params = {
                'keyword': keyword,
                'limit': min(limit, 100),
                'subId': 'ewall-search'
            }
            
            # 인증 헤더 생성
            headers = self._generate_auth_headers('GET', path)
            
            logger.info(f"Searching Coupang: {keyword}")
            
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            products = data.get('data', {}).get('productData', [])
            
            logger.info(f"Coupang: Found {len(products)} products for '{keyword}'")
            
            return self._normalize(products)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Coupang API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Coupang search failed: {e}")
            return []
    
    def get_product_detail(self, product_id: str) -> Optional[Dict]:
        """상품 상세 정보 조회"""
        try:
            path = f"/v2/providers/affiliate_open_api/apis/openapi/v1/products/{product_id}"
            url = self.base_url + path
            
            headers = self._generate_auth_headers('GET', path)
            
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            return data.get('data')
            
        except Exception as e:
            logger.error(f"Failed to get Coupang product detail: {e}")
            return None
    
    def generate_deeplink(self, product_url: str, sub_id: str = 'ewall') -> str:
        """딥링크 생성 (수수료 추적용)
        
        Args:
            product_url: 쿠팡 상품 URL
            sub_id: 서브 ID (트래킹용)
        
        Returns:
            제휴 딥링크
        """
        try:
            path = "/v2/providers/affiliate_open_api/apis/openapi/v1/deeplink"
            url = self.base_url + path
            
            headers = self._generate_auth_headers('POST', path)
            headers['Content-Type'] = 'application/json'
            
            payload = {
                'coupangUrls': [product_url],
                'subId': sub_id
            }
            
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            
            data = response.json()
            deeplinks = data.get('data', [])
            
            if deeplinks:
                return deeplinks[0].get('shortenUrl', product_url)
            
            return product_url
            
        except Exception as e:
            logger.error(f"Failed to generate Coupang deeplink: {e}")
            return product_url
    
    def _generate_auth_headers(self, method: str, path: str) -> Dict[str, str]:
        """쿠팡 API 인증 헤더 생성
        
        HMAC SHA256 서명 방식
        """
        datetime_str = datetime.utcnow().strftime('%y%m%d') + 'T' + datetime.utcnow().strftime('%H%M%S') + 'Z'
        
        # 서명 메시지 생성
        message = datetime_str + method + path
        
        # HMAC-SHA256 서명
        signature = hmac.new(
            self.secret_key.encode('utf-8'),
            message.encode('utf-8'),
            hashlib.sha256
        ).hexdigest()
        
        return {
            'Authorization': f'CEA algorithm=HmacSHA256, access-key={self.access_key}, signed-date={datetime_str}, signature={signature}',
            'Content-Type': 'application/json;charset=UTF-8'
        }
    
    def _normalize(self, products: List[Dict]) -> List[Dict]:
        """쿠팡 응답 데이터 정규화
        
        쿠팡 API 응답 형식:
        {
            "productId": 상품 ID,
            "productName": "상품명",
            "productImage": "이미지 URL",
            "productPrice": 판매가,
            "productUrl": "상품 URL",
            "categoryName": "카테고리",
            "isRocket": true/false,
            "isFreeShipping": true/false,
            "discountRate": 할인율
        }
        """
        normalized = []
        
        for product in products:
            try:
                product_id = str(product.get('productId', ''))
                title = product.get('productName', '')
                price = int(product.get('productPrice', 0))
                discount_rate = int(product.get('discountRate', 0))
                
                # 원가 계산
                original_price = price
                if discount_rate > 0:
                    original_price = int(price / (1 - discount_rate / 100))
                
                # 브랜드 추출 (제목에서)
                brand = self._extract_brand(title)
                
                # 카테고리 매핑
                category = self._map_category(product.get('categoryName', ''))
                
                # 딥링크 생성 (수수료 추적)
                product_url = product.get('productUrl', '')
                deeplink = self.generate_deeplink(product_url, f'ewall-{category}')
                
                normalized.append({
                    'platform': 'coupang',
                    'product_id': product_id,
                    'title': title,
                    'brand': brand,
                    'price': price,
                    'original_price': original_price,
                    'discount_rate': discount_rate,
                    'image_url': product.get('productImage', ''),
                    'product_url': deeplink,  # 딥링크 사용
                    'category': category,
                    'seller': '쿠팡',
                    'is_rocket': product.get('isRocket', False),
                    'free_shipping': product.get('isFreeShipping', False),
                    'in_stock': True,
                    'score': 0.0,
                })
                
            except Exception as e:
                logger.error(f"Failed to normalize Coupang item: {e}")
                continue
        
        return normalized
    
    def _extract_brand(self, title: str) -> str:
        """제목에서 브랜드 추출"""
        brands = [
            '노스페이스', '파타고니아', '아크테릭스', '밀레', '마무트',
            '코오롱스포츠', '네파', '블랙야크', '아이더', '케이투',
            'THE NORTH FACE', 'PATAGONIA', 'ARCTERYX', 'MILLET'
        ]
        
        title_lower = title.lower()
        for brand in brands:
            if brand.lower() in title_lower:
                return brand
        
        # 첫 단어를 브랜드로 가정
        words = title.split()
        return words[0] if words else ''
    
    def _map_category(self, category_name: str) -> str:
        """쿠팡 카테고리를 E-wall 카테고리로 매핑"""
        category_lower = category_name.lower()
        
        if '다운' in category_lower or '패딩' in category_lower:
            return 'down'
        elif '슬랙스' in category_lower:
            return 'slacks'
        elif '청바지' in category_lower or '진' in category_lower:
            return 'jeans'
        elif '맨투맨' in category_lower or '크루넥' in category_lower:
            return 'crewneck'
        elif '긴팔' in category_lower:
            return 'long-sleeve'
        elif '코트' in category_lower or '자켓' in category_lower:
            return 'coat'
        else:
            return 'generic'
    
    def search_outlet_products(self, brands: List[str] = None, min_discount: int = 30) -> List[Dict]:
        """이월상품 검색 (할인율 높은 상품)
        
        Args:
            brands: 브랜드 리스트
            min_discount: 최소 할인율
        
        Returns:
            이월상품 리스트
        """
        if brands is None:
            brands = ['노스페이스', '파타고니아', '아크테릭스', '밀레']
        
        all_products = []
        
        for brand in brands:
            # 이월 키워드 조합
            keywords = [
                f"{brand} 이월",
                f"{brand} 아울렛",
                f"{brand} SALE"
            ]
            
            for keyword in keywords:
                products = self.search(keyword, limit=100)
                
                # 할인율 필터링
                outlet_products = [
                    p for p in products 
                    if p['discount_rate'] >= min_discount
                ]
                
                all_products.extend(outlet_products)
                logger.info(f"'{keyword}': {len(outlet_products)} outlet products")
        
        # 중복 제거
        unique_products = {p['product_id']: p for p in all_products}
        
        result = list(unique_products.values())
        logger.info(f"Total unique Coupang outlet products: {len(result)}")
        
        return result
