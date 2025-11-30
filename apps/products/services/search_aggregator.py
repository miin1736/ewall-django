"""
Multi-Platform Search Aggregator
여러 쇼핑 플랫폼의 검색 결과를 통합하여 제공
"""
import logging
from typing import List, Dict, Any, Optional
from decimal import Decimal
from concurrent.futures import ThreadPoolExecutor, as_completed
from django.core.cache import cache
from .crawlers import CoupangCrawler, NaverCrawler

logger = logging.getLogger(__name__)

# 공식 API 크롤러 임포트 (선택적)
try:
    from .crawlers.naver_shopping_crawler import NaverShoppingCrawler
    NAVER_SHOPPING_AVAILABLE = True
except ImportError:
    NAVER_SHOPPING_AVAILABLE = False

try:
    from .crawlers.coupang_partners_crawler import CoupangPartnersCrawler
    COUPANG_PARTNERS_AVAILABLE = True
except ImportError:
    COUPANG_PARTNERS_AVAILABLE = False


class SearchAggregator:
    """멀티플랫폼 검색 통합 서비스
    
    여러 쇼핑몰에서 동시에 검색하고 결과를 통합, 정규화, 랭킹
    
    Features:
        - 병렬 검색 (ThreadPoolExecutor)
        - 중복 제거 (제목 유사도 기반)
        - 점수 기반 랭킹
        - Redis 캐싱
    
    Supported APIs:
        - 네이버 쇼핑 검색 API (공식)
        - 쿠팡 파트너스 API (공식)
        - Coupang/Naver 크롤러 (백업)
    """
    
    def __init__(self, use_official_apis: bool = True):
        """
        Args:
            use_official_apis: True이면 공식 API 우선 사용
        """
        self.crawlers = {}
        
        # 네이버: 공식 API 우선, 없으면 크롤러
        if use_official_apis and NAVER_SHOPPING_AVAILABLE:
            self.crawlers['naver'] = NaverShoppingCrawler()
            logger.info("Using Naver Shopping API (Official)")
        else:
            self.crawlers['naver'] = NaverCrawler()
            logger.info("Using Naver Crawler (Fallback)")
        
        # 쿠팡: 공식 API 우선, 없으면 크롤러
        if use_official_apis and COUPANG_PARTNERS_AVAILABLE:
            self.crawlers['coupang'] = CoupangPartnersCrawler()
            logger.info("Using Coupang Partners API (Official)")
        else:
            self.crawlers['coupang'] = CoupangCrawler()
            logger.info("Using Coupang Crawler (Fallback)")
    
    def search(
        self,
        keyword: str,
        platforms: Optional[List[str]] = None,
        limit: int = 50,
        **filters
    ) -> Dict[str, Any]:
        """통합 검색
        
        Args:
            keyword: 검색 키워드
            platforms: 검색할 플랫폼 리스트 (None이면 전체)
            limit: 플랫폼당 최대 결과 수
            **filters: 필터 옵션
                - min_price: 최소 가격
                - max_price: 최대 가격
                - min_discount: 최소 할인율
                - brand: 브랜드 필터
                - category: 카테고리 필터
        
        Returns:
            {
                'keyword': '검색어',
                'total': 100,
                'platforms': {
                    'coupang': 45,
                    'naver': 55
                },
                'products': [...],
                'cached': False
            }
        """
        # 캐시 확인
        cache_key = self._generate_cache_key(keyword, platforms, limit, **filters)
        cached_result = cache.get(cache_key)
        
        if cached_result:
            logger.info(f"Cache hit for search: {keyword}")
            cached_result['cached'] = True
            return cached_result
        
        # 검색할 플랫폼 결정
        if platforms is None:
            platforms = list(self.crawlers.keys())
        
        # 병렬 검색 실행
        all_products = self._parallel_search(keyword, platforms, limit)
        
        # 필터링
        if filters:
            all_products = self._apply_filters(all_products, **filters)
        
        # 중복 제거
        unique_products = self._deduplicate(all_products)
        
        # 점수 계산 및 정렬
        ranked_products = self._rank_products(unique_products)
        
        # 플랫폼별 통계
        platform_counts = self._count_by_platform(ranked_products)
        
        # 결과 구성
        result = {
            'keyword': keyword,
            'total': len(ranked_products),
            'platforms': platform_counts,
            'products': ranked_products,
            'cached': False
        }
        
        # 캐시 저장 (5분)
        cache.set(cache_key, result, timeout=300)
        
        logger.info(
            f"Search complete: keyword='{keyword}', "
            f"total={result['total']}, platforms={platform_counts}"
        )
        
        return result
    
    def _parallel_search(
        self,
        keyword: str,
        platforms: List[str],
        limit: int
    ) -> List[Dict[str, Any]]:
        """병렬로 여러 플랫폼 검색
        
        ThreadPoolExecutor를 사용하여 동시 검색
        """
        all_products = []
        
        with ThreadPoolExecutor(max_workers=len(platforms)) as executor:
            # 각 플랫폼에 대한 Future 생성
            future_to_platform = {}
            
            for platform in platforms:
                crawler = self.crawlers.get(platform)
                if not crawler:
                    logger.warning(f"Unknown platform: {platform}")
                    continue
                
                future = executor.submit(crawler.search, keyword, limit=limit)
                future_to_platform[future] = platform
            
            # 결과 수집
            for future in as_completed(future_to_platform):
                platform = future_to_platform[future]
                try:
                    products = future.result(timeout=30)
                    logger.info(f"{platform}: {len(products)} products")
                    all_products.extend(products)
                except Exception as e:
                    logger.error(f"Search failed for {platform}: {e}")
        
        return all_products
    
    def _apply_filters(
        self,
        products: List[Dict[str, Any]],
        **filters
    ) -> List[Dict[str, Any]]:
        """필터 적용"""
        filtered = products
        
        # 가격 필터
        min_price = filters.get('min_price')
        if min_price is not None:
            min_price = Decimal(str(min_price))
            filtered = [p for p in filtered if p['price'] >= min_price]
        
        max_price = filters.get('max_price')
        if max_price is not None:
            max_price = Decimal(str(max_price))
            filtered = [p for p in filtered if p['price'] <= max_price]
        
        # 할인율 필터
        min_discount = filters.get('min_discount')
        if min_discount is not None:
            min_discount = Decimal(str(min_discount))
            filtered = [
                p for p in filtered 
                if p.get('discount_rate', Decimal('0')) >= min_discount
            ]
        
        # 브랜드 필터
        brand = filters.get('brand')
        if brand:
            filtered = [
                p for p in filtered 
                if p.get('brand', '').lower() == brand.lower()
            ]
        
        # 카테고리 필터
        category = filters.get('category')
        if category:
            filtered = [
                p for p in filtered 
                if p.get('category') == category
            ]
        
        return filtered
    
    def _deduplicate(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """중복 상품 제거
        
        제목 유사도 기반으로 동일 상품 판단
        (간단한 구현: 제목의 첫 30자가 비슷하면 중복으로 간주)
        """
        from difflib import SequenceMatcher
        
        unique_products = []
        seen_titles = []
        
        for product in products:
            title = product['title'][:50]  # 첫 50자
            
            # 기존 제목과 유사도 확인
            is_duplicate = False
            for seen_title in seen_titles:
                similarity = SequenceMatcher(None, title, seen_title).ratio()
                if similarity > 0.85:  # 85% 이상 유사하면 중복
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                unique_products.append(product)
                seen_titles.append(title)
        
        logger.info(
            f"Deduplication: {len(products)} -> {len(unique_products)} "
            f"({len(products) - len(unique_products)} duplicates removed)"
        )
        
        return unique_products
    
    def _rank_products(self, products: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """상품 점수 계산 및 정렬
        
        점수 계산 기준:
            - 할인율 (40%)
            - 평점 (30%)
            - 리뷰 수 (20%)
            - 배송 정보 (10%)
        """
        for product in products:
            score = 0.0
            
            # 1. 할인율 점수 (0-40점)
            discount_rate = float(product.get('discount_rate', 0))
            discount_score = min(discount_rate, 100) * 0.4
            score += discount_score
            
            # 2. 평점 점수 (0-30점)
            rating = product.get('rating', 0.0)
            rating_score = (rating / 5.0) * 30
            score += rating_score
            
            # 3. 리뷰 수 점수 (0-20점)
            review_count = product.get('review_count', 0)
            # 로그 스케일 (100개 리뷰 = 10점, 1000개 = 15점, 10000개 = 20점)
            import math
            if review_count > 0:
                review_score = min(math.log10(review_count) * 5, 20)
            else:
                review_score = 0
            score += review_score
            
            # 4. 배송 정보 점수 (0-10점)
            delivery_info = product.get('delivery_info', '').lower()
            if '로켓배송' in delivery_info or 'rocket' in delivery_info:
                delivery_score = 10
            elif '무료배송' in delivery_info or 'free' in delivery_info:
                delivery_score = 7
            else:
                delivery_score = 0
            score += delivery_score
            
            # 점수 저장
            product['score'] = round(score, 2)
        
        # 점수 기준 내림차순 정렬
        ranked = sorted(products, key=lambda p: p['score'], reverse=True)
        
        return ranked
    
    def _count_by_platform(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """플랫폼별 상품 수 집계"""
        counts = {}
        for product in products:
            platform = product['platform']
            counts[platform] = counts.get(platform, 0) + 1
        return counts
    
    def _generate_cache_key(
        self,
        keyword: str,
        platforms: Optional[List[str]],
        limit: int,
        **filters
    ) -> str:
        """캐시 키 생성"""
        import hashlib
        import json
        
        # 캐시 키 생성용 데이터
        cache_data = {
            'keyword': keyword,
            'platforms': sorted(platforms) if platforms else 'all',
            'limit': limit,
            'filters': filters
        }
        
        # JSON 직렬화 후 해시
        json_str = json.dumps(cache_data, sort_keys=True)
        hash_str = hashlib.md5(json_str.encode()).hexdigest()
        
        return f"search_agg:{hash_str}"
    
    def get_available_platforms(self) -> List[str]:
        """사용 가능한 플랫폼 리스트"""
        return list(self.crawlers.keys())
    
    def add_crawler(self, platform: str, crawler):
        """새 크롤러 추가"""
        self.crawlers[platform] = crawler
        logger.info(f"Added crawler for platform: {platform}")
