"""
네이버 쇼핑 API를 통한 고품질 이월상품 데이터 로더

이 스크립트는 다음 전략으로 최적의 이월상품 데이터를 수집합니다:
1. 브랜드 + 검색어 조합으로 다각도 검색
2. 할인율, 가격대, 브랜드 검증으로 품질 필터링
3. 중복 제거 (productId 기반)
4. 카테고리/브랜드 자동 매핑 및 검증
5. 이미지 품질 검증
"""

import os
import sys
import django
from pathlib import Path

# Django 설정
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')
django.setup()

from apps.products.models import GenericProduct, Brand, Category
from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler
from decimal import Decimal
from django.utils.text import slugify
import time
import re


class AdvancedOutletLoader:
    """고급 이월상품 로더"""
    
    # 신뢰할 수 있는 고급 브랜드 목록
    PREMIUM_BRANDS = [
        '노스페이스', 'The North Face',
        '파타고니아', 'Patagonia',
        '아크테릭스', "Arc'teryx",
        '마무트', 'Mammut',
        '코오롱스포츠',
        '밀레', 'Millet',
        '나이키', 'Nike',
        '아디다스', 'Adidas',
        '뉴발란스', 'New Balance',
        '살로몬', 'Salomon',
        '콜럼비아', 'Columbia',
        '잭울프스킨', 'Jack Wolfskin',
    ]
    
    # 검색 패턴 (브랜드 x 키워드 조합)
    SEARCH_KEYWORDS = [
        '이월',
        '아울렛',
        '재고',
        '세일',
        '할인',
    ]
    
    # 카테고리별 추가 검색어
    CATEGORY_KEYWORDS = {
        'outer': ['패딩', '점퍼', '자켓', '코트', '파카'],
        'top': ['티셔츠', '맨투맨', '후드', '니트', '셔츠'],
        'bottom': ['팬츠', '조거', '레깅스', '반바지'],
        'shoes': ['등산화', '트레일', '런닝화', '스니커즈'],
        'accessories': ['백팩', '가방', '모자', '장갑'],
    }
    
    # 최소 품질 기준
    MIN_DISCOUNT_RATE = 30  # 최소 할인율 30%
    MIN_PRICE = 1000  # 최소 가격 1,000원 (디버깅용으로 낮춤)
    MAX_PRICE = 100000000  # 최대 가격 1억원 (거의 제한 없음)
    
    def __init__(self):
        self.crawler = NaverShoppingCrawler()
        self.stats = {
            'searched': 0,
            'filtered': 0,
            'duplicates': 0,
            'created': 0,
            'updated': 0,
            'errors': 0,
        }
        self.seen_product_ids = set()
    
    def calculate_discount_rate(self, item):
        """할인율 계산"""
        try:
            lprice = int(item.get('lprice', 0))
            hprice = int(item.get('hprice', 0))
            
            if hprice and lprice and hprice > lprice:
                return ((hprice - lprice) / hprice) * 100
            return 0
        except (ValueError, ZeroDivisionError):
            return 0
    
    def is_premium_brand(self, title, brand):
        """프리미엄 브랜드 여부 확인"""
        search_text = f"{title} {brand}".lower()
        
        for premium_brand in self.PREMIUM_BRANDS:
            if premium_brand.lower() in search_text:
                return True
        return False
    
    def validate_product(self, item):
        """상품 데이터 검증 (정규화된 데이터 기준)"""
        try:
            # 1. 가격 검증 (이미 정규화된 데이터이므로 정수형)
            lprice = item.get('price', 0)
            hprice = item.get('original_price', 0)
            
            # 디버그: 첫 번째 상품만 출력
            if not hasattr(self, '_debug_printed'):
                print(f"\n>>> DEBUG: price={lprice}, original_price={hprice}")
                print(f">>> DEBUG: MIN_PRICE={self.MIN_PRICE}, MAX_PRICE={self.MAX_PRICE}\n")
                self._debug_printed = True
            
            if not (self.MIN_PRICE <= lprice <= self.MAX_PRICE):
                return False, "가격 범위 벗어남"
            
            # 2. 할인율 검증 (hprice가 있는 경우만)
            if hprice > 0:  # 정가 정보가 있는 경우
                discount_rate = item.get('discount_rate', 0)
                if discount_rate < self.MIN_DISCOUNT_RATE:
                    return False, f"할인율 부족 ({discount_rate:.1f}%)"
            # hprice가 0이면 할인율 검증 스킵 (이월/아울렛 검색어 자체가 할인 의미)
            
            # 3. 브랜드 검증 (선택적)
            title = item.get('title', '')
            brand = item.get('brand', '')
            # 프리미엄 브랜드 검증은 선택적으로 변경
            # if not self.is_premium_brand(title, brand):
            #     return False, "프리미엄 브랜드 아님"
            
            # 4. 중복 검증
            product_id = item.get('product_id')
            if product_id in self.seen_product_ids:
                self.stats['duplicates'] += 1
                return False, "중복 상품"
            
            # 5. 필수 필드 검증
            if not item.get('image_url'):
                return False, "이미지 없음"
            
            if not item.get('product_url'):
                return False, "구매 링크 없음"
            
            return True, "OK"
            
        except Exception as e:
            return False, f"검증 오류: {str(e)}"
    
    def normalize_brand_name(self, title, brand):
        """브랜드명 정규화"""
        search_text = f"{title} {brand}".lower()
        
        # 영문명 -> 한글명 매핑
        brand_mapping = {
            'the north face': '노스페이스',
            'patagonia': '파타고니아',
            "arc'teryx": '아크테릭스',
            'arcteryx': '아크테릭스',
            'mammut': '마무트',
            'millet': '밀레',
            'nike': '나이키',
            'adidas': '아디다스',
            'new balance': '뉴발란스',
            'salomon': '살로몬',
            'columbia': '콜럼비아',
            'jack wolfskin': '잭울프스킨',
        }
        
        for eng, kor in brand_mapping.items():
            if eng in search_text:
                return kor
        
        # 원본 브랜드 반환
        return brand if brand else '기타'
    
    def extract_category_from_title(self, title):
        """제목에서 카테고리 추출"""
        title_lower = title.lower()
        
        category_keywords = {
            'outer': ['패딩', '점퍼', '자켓', 'jacket', '코트', 'coat', '파카', 'parka'],
            'top': ['티셔츠', 'tshirt', 't-shirt', '맨투맨', '후드', 'hood', '니트', '셔츠', 'shirt'],
            'bottom': ['팬츠', 'pants', '조거', 'jogger', '레깅스', 'leggings', '반바지', 'shorts'],
            'shoes': ['신발', '등산화', '트레일', 'trail', '런닝', 'running', '스니커즈', 'sneakers'],
            'accessories': ['백팩', 'backpack', '가방', 'bag', '모자', 'cap', '장갑', 'glove'],
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in title_lower:
                    return category
        
        return 'outer'  # 기본값
    
    def search_with_pattern(self, brand, keyword, limit=20):
        """브랜드 + 키워드 조합 검색"""
        query = f"{brand} {keyword}"
        print(f"\n🔍 검색: {query}")
        
        try:
            results = self.crawler.search(
                keyword=query,
                limit=limit,
                sort='sim'  # 정확도순
            )
            
            self.stats['searched'] += len(results)
            print(f"   ✓ {len(results)}개 상품 발견")
            
            return results
            
        except Exception as e:
            print(f"   ✗ 검색 오류: {str(e)}")
            return []
    
    def search_by_category(self, category_name, limit=15):
        """카테고리별 검색"""
        keywords = self.CATEGORY_KEYWORDS.get(category_name, [])
        results = []
        
        for keyword in keywords[:3]:  # 상위 3개 키워드만
            query = f"{keyword} 이월"
            print(f"\n🔍 카테고리 검색: {query}")
            
            try:
                items = self.crawler.search(
                    keyword=query,
                    limit=limit,
                    sort='sim'
                )
                results.extend(items)
                self.stats['searched'] += len(items)
                print(f"   ✓ {len(items)}개 상품 발견")
                
                time.sleep(0.2)  # API 호출 제한 고려
                
            except Exception as e:
                print(f"   ✗ 검색 오류: {str(e)}")
        
        return results
    
    def save_product(self, item):
        """상품 저장 (중복 체크 포함) - 정규화된 데이터 기준"""
        try:
            # 브랜드명 정규화
            normalized_brand = self.normalize_brand_name(
                item.get('title', ''),
                item.get('brand', '')
            )
            
            # 브랜드 가져오기 또는 생성
            brand, _ = Brand.objects.get_or_create(
                name=normalized_brand,
                defaults={'slug': normalized_brand.lower().replace(' ', '-')}
            )
            
            # 카테고리 추출
            category_slug = item.get('category', 'outer')
            category = Category.objects.filter(slug=category_slug).first()
            
            # 할인율
            discount_rate = item.get('discount_rate', 0)
            
            # 상품 저장 (upsert) - product_id를 primary key로 사용
            # slug를 product_id와 조합하여 unique하게 생성
            title_slug = slugify(item.get('title', '')[:50])  # 제목 앞부분만 사용
            unique_slug = f"{title_slug}-{item.get('product_id')}" if title_slug else item.get('product_id')
            
            product, created = GenericProduct.objects.update_or_create(
                id=item.get('product_id'),  # primary key (id 필드)
                defaults={
                    'title': item.get('title', ''),
                    'brand': brand,
                    'category': category,
                    'price': Decimal(str(item.get('price', 0))),
                    'original_price': Decimal(str(item.get('original_price', 0))) if item.get('original_price') else Decimal(str(item.get('price', 0))),
                    'discount_rate': Decimal(str(discount_rate)),
                    'image_url': item.get('image_url', ''),
                    'deeplink': item.get('product_url', ''),
                    'source': 'naver',
                    'in_stock': item.get('in_stock', True),
                    'seller': item.get('seller', ''),
                    'slug': unique_slug,
                    'currency': 'KRW',
                    'score': 0.0,
                }
            )
            
            if created:
                self.stats['created'] += 1
                print(f"   ✓ 신규: {product.title[:50]}... ({product.price:,}원, {discount_rate:.0f}% 할인)")
            else:
                self.stats['updated'] += 1
                print(f"   ↻ 업데이트: {product.title[:50]}... ({product.price:,}원)")
            
            # 중복 방지용 ID 추가
            if item.get('product_id'):
                self.seen_product_ids.add(item.get('product_id'))
            
            return True
            
        except Exception as e:
            self.stats['errors'] += 1
            print(f"   ✗ 저장 오류: {str(e)}")
            return False
    
    def run_comprehensive_search(self):
        """종합 검색 실행"""
        print("=" * 70)
        print("🎯 네이버 쇼핑 API 고급 이월상품 수집 시작")
        print("=" * 70)
        
        # 1. 브랜드별 검색
        print("\n\n📦 1단계: 프리미엄 브랜드 이월상품 검색")
        print("-" * 70)
        
        for brand in self.PREMIUM_BRANDS[:8]:  # 상위 8개 브랜드
            for keyword in self.SEARCH_KEYWORDS[:3]:  # 상위 3개 키워드
                results = self.search_with_pattern(brand, keyword, limit=20)
                
                # 품질 필터링 및 저장
                debug_count = 0
                for item in results:
                    is_valid, reason = self.validate_product(item)
                    
                    if is_valid:
                        self.save_product(item)
                    else:
                        self.stats['filtered'] += 1
                        # 디버깅: 처음 3개만 출력
                        if debug_count < 3:
                            price = item.get('price', 0)
                            title = item.get('title', '')[:30]
                            print(f"   - 필터링: {reason} | {title}... ({price:,}원)")
                            debug_count += 1
                
                time.sleep(0.15)  # API 호출 제한 (일 25,000건)
        
        # 2. 카테고리별 검색
        print("\n\n📂 2단계: 카테고리별 이월상품 검색")
        print("-" * 70)
        
        for category in ['outer', 'top', 'shoes']:  # 주요 카테고리
            results = self.search_by_category(category, limit=15)
            
            for item in results:
                is_valid, reason = self.validate_product(item)
                
                if is_valid:
                    self.save_product(item)
                else:
                    self.stats['filtered'] += 1
            
            time.sleep(0.2)
        
        # 3. 최종 통계
        self.print_statistics()
    
    def print_statistics(self):
        """수집 통계 출력"""
        print("\n\n" + "=" * 70)
        print("📊 수집 완료 통계")
        print("=" * 70)
        print(f"🔍 검색된 상품: {self.stats['searched']:,}개")
        print(f"✅ 품질 검증 통과: {self.stats['created'] + self.stats['updated']:,}개")
        print(f"   - 신규 생성: {self.stats['created']:,}개")
        print(f"   - 업데이트: {self.stats['updated']:,}개")
        print(f"🚫 필터링된 상품: {self.stats['filtered']:,}개")
        print(f"♻️  중복 제거: {self.stats['duplicates']:,}개")
        print(f"❌ 오류: {self.stats['errors']:,}개")
        print("=" * 70)
        
        # 품질 통과율 계산
        if self.stats['searched'] > 0:
            pass_rate = ((self.stats['created'] + self.stats['updated']) / self.stats['searched']) * 100
            print(f"\n💎 품질 통과율: {pass_rate:.1f}%")
        
        print("\n✨ 다음 단계:")
        print("1. python manage.py runserver")
        print("2. http://localhost:8000/admin/products/genericproduct/ 에서 상품 확인")
        print("3. 홈페이지에 이월상품 페이지 구현")


if __name__ == '__main__':
    loader = AdvancedOutletLoader()
    loader.run_comprehensive_search()
