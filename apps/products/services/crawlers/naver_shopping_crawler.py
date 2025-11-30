"""
네이버 쇼핑 검색 API 크롤러
공식 API로 실제 상품 데이터 수집
"""
import requests
import logging
from typing import List, Dict, Optional
from django.conf import settings
import re

logger = logging.getLogger(__name__)


class NaverShoppingCrawler:
    """네이버 쇼핑 검색 API 크롤러"""
    
    # 브랜드명 → slug 매핑 (한글 브랜드의 정확한 영문 slug)
    BRAND_SLUG_MAPPING = {
        '내셔널지오그래픽': 'national-geographic',
        'MC2세인트바스': 'mc2-saint-barth',
        '디스커버리익스페디션': 'discovery-expedition',
        '몽벨': 'montbell',
        '밀레': 'millet',
        '아이더': 'eider',
        '알트라': 'altra',
        '트렉스타': 'treksta',
        '피엘라벤': 'fjallraven',
        '블랙야크': 'blackyak',
        '코오롱스포츠': 'kolon-sport',
        '네파': 'nepa',
        '노스페이스': 'the-north-face',
        '파타고니아': 'patagonia',
        '아크테릭스': 'arcteryx',
        '마무트': 'mammut',
        '살로몬': 'salomon',
        '호그롤프스': 'haglofs',
        '잭울프스킨': 'jack-wolfskin',
        '컬럼비아': 'columbia',
        'K2': 'k2',
        'THE NORTH FACE': 'the-north-face',
        'PATAGONIA': 'patagonia',
        'ARCTERYX': 'arcteryx',
        'MAMMUT': 'mammut',
        'SALOMON': 'salomon',
        'COLUMBIA': 'columbia',
    }
    
    def __init__(self):
        self.client_id = getattr(settings, 'NAVER_CLIENT_ID', '')
        self.client_secret = getattr(settings, 'NAVER_CLIENT_SECRET', '')
        self.base_url = "https://openapi.naver.com/v1/search/shop.json"
        
        if not self.client_id or not self.client_secret:
            logger.warning("Naver API credentials not configured")
    
    def search(self, keyword: str, limit: int = 100, sort: str = 'sim') -> List[Dict]:
        """네이버 쇼핑 검색
        
        Args:
            keyword: 검색 키워드
            limit: 최대 결과 수 (최대 100)
            sort: 정렬 방식 (sim: 유사도, date: 날짜, asc: 가격낮은순, dsc: 가격높은순)
        
        Returns:
            정규화된 상품 리스트
        """
        if not self.client_id or not self.client_secret:
            logger.error("Naver API credentials missing")
            return []
        
        try:
            headers = {
                'X-Naver-Client-Id': self.client_id,
                'X-Naver-Client-Secret': self.client_secret
            }
            
            params = {
                'query': keyword,
                'display': min(limit, 100),
                'sort': sort,
                'exclude': 'used:rental'  # 중고/대여 제외
            }
            
            logger.info(f"Searching Naver Shopping: {keyword}")
            
            response = requests.get(
                self.base_url,
                headers=headers,
                params=params,
                timeout=30
            )
            response.raise_for_status()
            
            data = response.json()
            items = data.get('items', [])
            
            logger.info(f"Naver: Found {len(items)} products for '{keyword}'")
            
            return self._normalize(items)
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Naver API request failed: {e}")
            return []
        except Exception as e:
            logger.error(f"Naver search failed: {e}")
            return []
    
    def _normalize(self, items: List[Dict]) -> List[Dict]:
        """네이버 응답 데이터 정규화
        
        네이버 API 응답 형식:
        {
            "title": "상품명 (HTML 태그 포함)",
            "link": "상품 URL",
            "image": "이미지 URL",
            "lprice": "최저가",
            "hprice": "최고가",
            "mallName": "쇼핑몰명",
            "productId": "상품 ID",
            "productType": "1:일반, 2:중고, 3:단종, 4:판매예정",
            "brand": "브랜드",
            "maker": "제조사",
            "category1": "대분류",
            "category2": "중분류",
            "category3": "소분류",
            "category4": "세분류"
        }
        """
        normalized = []
        
        for item in items:
            try:
                # HTML 태그 제거
                title = self._clean_title(item.get('title', ''))
                
                # 가격 정보 (문자열 → 정수 변환, 빈 문자열은 0)
                lprice_str = item.get('lprice', '') or '0'
                hprice_str = item.get('hprice', '') or '0'
                
                lprice = int(lprice_str) if lprice_str else 0
                hprice = int(hprice_str) if hprice_str else lprice
                
                # 할인율 계산
                discount_rate = 0
                if hprice > lprice > 0:
                    discount_rate = int(((hprice - lprice) / hprice) * 100)
                
                # 브랜드 추출
                # 1순위: API의 brand 필드 (공식 제공)
                brand = item.get('brand', '').strip()
                
                # 2순위: maker 필드 (제조사)
                if not brand:
                    brand = item.get('maker', '').strip()
                
                # 3순위: 제목에서 알려진 브랜드 추출
                if not brand:
                    brand = self._extract_brand_from_title(title)
                
                # 최종: 브랜드 없으면 UNKNOWN
                if not brand:
                    brand = 'UNKNOWN'
                
                # 카테고리 매핑
                category = self._map_category(item)
                
                normalized.append({
                    'platform': 'naver',
                    'product_id': str(item.get('productId', '')),
                    'title': title,
                    'brand': brand,
                    'price': lprice,
                    'original_price': hprice,
                    'discount_rate': discount_rate,
                    'image_url': item.get('image', ''),
                    'product_url': item.get('link', ''),
                    'category': category,
                    'seller': item.get('mallName', ''),
                    'maker': item.get('maker', ''),
                    'in_stock': item.get('productType') == '1',  # 1: 일반 상품
                    'score': 0.0,
                })
                
            except Exception as e:
                logger.error(f"Failed to normalize Naver item: {e}")
                continue
        
        return normalized
    
    def _clean_title(self, title: str) -> str:
        """HTML 태그 및 특수문자 제거"""
        # HTML 태그 제거
        title = re.sub(r'<[^>]+>', '', title)
        # HTML 엔티티 디코드
        title = title.replace('&lt;', '<').replace('&gt;', '>')
        title = title.replace('&amp;', '&').replace('&quot;', '"')
        title = title.replace('&#39;', "'")
        return title.strip()
    
    def _extract_brand_from_title(self, title: str) -> str:
        """제목에서 브랜드 추출
        
        알려진 브랜드 리스트에서 매칭을 시도하되,
        찾지 못하면 빈 문자열 반환 (UNKNOWN 처리는 상위 레이어에서)
        """
        # 주요 아웃도어 브랜드 (영문/한글)
        known_brands = [
            # 한글 브랜드명
            '노스페이스', '파타고니아', '아크테릭스', '밀레', '마무트',
            '코오롱스포츠', '네파', '블랙야크', '아이더', '케이투',
            '살로몬', '호그롤프스', '잭울프스킨', '컬럼비아', '디스커버리',
            '피엘라벤', '트렉스타', '알트라', '내셔널지오그래픽', '몽벨',
            'MC2세인트바스', '블랙다이아몬드', '스카르파', '비에스래빗',
            '스톤아일랜드', '알타이카', '콜마운틴',
            
            # 영문 브랜드명
            'THE NORTH FACE', 'PATAGONIA', 'ARCTERYX', "ARC'TERYX",
            'MILLET', 'MAMMUT', 'K2', 'SALOMON', 'COLUMBIA', 'DISCOVERY',
            'FJALLRAVEN', 'TREKSTA', 'ALTRA', 'BLACK DIAMOND',
            'SCARPA', 'NATIONAL GEOGRAPHIC', 'MONTBELL', 'MC2',
            'STONE ISLAND', 'KOLON SPORT', 'NEPA', 'BLACKYAK',
            'EIDER', 'HAGLOFS', 'JACK WOLFSKIN'
        ]
        
        title_lower = title.lower()
        
        # 브랜드명 매칭 (대소문자 무시)
        for brand in known_brands:
            if brand.lower() in title_lower:
                return brand
        
        # 찾지 못하면 빈 문자열 반환
        return ''
    
    def _map_category(self, item: Dict, use_ai: bool = False, product_id: str = None) -> str:
        """네이버 카테고리를 E-wall 카테고리로 매핑
        
        Args:
            item: 네이버 API 응답 아이템
            use_ai: AI 분류기 사용 여부 (임베딩 생성 후)
            product_id: 상품 ID (AI 분류용)
        
        Returns:
            카테고리 slug
        """
        category1 = item.get('category1', '').lower()
        category2 = item.get('category2', '').lower()
        category3 = item.get('category3', '').lower()
        title = item.get('title', '').lower()
        
        # 1차: API 카테고리 우선 검색
        api_category = f"{category1} {category2} {category3}"
        
        if '다운' in api_category or '패딩' in api_category:
            return 'down'
        elif '슬랙스' in api_category:
            return 'slacks'
        elif '청바지' in api_category or '진' in api_category:
            return 'jeans'
        elif '맨투맨' in api_category or '크루넥' in api_category:
            return 'crewneck'
        elif '긴팔' in api_category or '티셔츠' in api_category:
            return 'long-sleeve'
        elif '코트' in api_category or '자켓' in api_category:
            return 'coat'
        
        # 2차: 상품명 키워드 분석 (API에 정보 없을 때)
        if '패딩' in title or '다운점퍼' in title or '덕다운' in title or '구스다운' in title:
            return 'down'
        elif '슬랙스' in title or '정장바지' in title:
            return 'slacks'
        elif '청바지' in title or '데님' in title or '진팬츠' in title:
            return 'jeans'
        elif '맨투맨' in title or '크루넥' in title or '스웨트셔츠' in title:
            return 'crewneck'
        elif '긴팔' in title or '롱슬리브' in title or '긴팔티' in title:
            return 'long-sleeve'
        elif '코트' in title or '자켓' in title or '점퍼' in title or '잠바' in title:
            return 'coat'
        
        # 3차: AI/ML 이미지 기반 분류 (임베딩 있을 때만)
        if use_ai and product_id:
            try:
                from apps.products.services.category_classifier import get_classifier
                classifier = get_classifier()
                ai_category = classifier.classify_product(product_id, item.get('title', ''))
                if ai_category != 'generic':
                    logger.info(f"🤖 AI 분류: {item.get('title', '')[:30]} → {ai_category}")
                    return ai_category
            except Exception as e:
                logger.warning(f"AI 분류 실패: {e}")
        
        # 4차: 분류 불가
        return 'generic'
    
    def search_outlet_products(self, brands: List[str] = None, limit_per_brand: int = 50) -> List[Dict]:
        """이월상품 전용 검색
        
        Args:
            brands: 검색할 브랜드 리스트
            limit_per_brand: 브랜드당 최대 상품 수
        
        Returns:
            이월상품 리스트
        """
        if brands is None:
            brands = [
                '노스페이스', '파타고니아', '아크테릭스', '밀레',
                '코오롱스포츠', '네파', '블랙야크', '아이더'
            ]
        
        all_products = []
        
        # 브랜드별 이월상품 검색
        for brand in brands:
            # 이월 키워드 조합
            keywords = [
                f"{brand} 이월",
                f"{brand} 아울렛",
                f"{brand} 세일",
                f"{brand} 할인"
            ]
            
            for keyword in keywords:
                products = self.search(keyword, limit=limit_per_brand, sort='dsc')  # 가격 높은순 (할인 전 가격)
                
                # 이월상품 필터링 (할인율 30% 이상)
                outlet_products = [p for p in products if p['discount_rate'] >= 30]
                
                all_products.extend(outlet_products)
                
                logger.info(f"'{keyword}': {len(outlet_products)} outlet products")
        
        # 중복 제거 (product_id 기준)
        unique_products = {}
        for product in all_products:
            pid = product['product_id']
            if pid not in unique_products:
                unique_products[pid] = product
        
        result = list(unique_products.values())
        logger.info(f"Total unique outlet products: {len(result)}")
        
        return result
    
    def get_brand_slug(self, brand_name: str) -> str:
        """브랜드명을 안전한 slug로 변환
        
        Args:
            brand_name: 브랜드명 (한글/영문)
        
        Returns:
            영문 slug (URL 안전)
        """
        # 매핑에 있으면 사용
        if brand_name in self.BRAND_SLUG_MAPPING:
            return self.BRAND_SLUG_MAPPING[brand_name]
        
        # 없으면 slugify (allow_unicode=False로 한글 제거)
        from django.utils.text import slugify
        slug = slugify(brand_name, allow_unicode=False)
        
        # slug가 비어있으면 (한글만 있는 경우) 'unknown-브랜드ID' 형식
        if not slug:
            slug = f'brand-{abs(hash(brand_name)) % 10000}'
        
        return slug
