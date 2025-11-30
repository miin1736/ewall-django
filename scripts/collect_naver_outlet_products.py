"""
네이버 쇼핑 API 이월상품 수집 스크립트
실행: python scripts/collect_naver_outlet_products.py
"""
import os
import sys
import django

# Django 설정
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler
from apps.products.models import GenericProduct, DownProduct, CoatProduct
from apps.core.models import Brand, Category
from django.utils import timezone
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def collect_outlet_products():
    """네이버 쇼핑에서 이월상품 수집"""
    
    crawler = NaverShoppingCrawler()
    
    # 이월상품 검색 키워드
    outlet_keywords = [
        '노스페이스 이월',
        '파타고니아 아울렛',
        '아크테릭스 세일',
        '밀레 이월상품',
        '코오롱스포츠 할인',
        '네파 아울렛',
        '블랙야크 세일',
    ]
    
    total_created = 0
    total_updated = 0
    total_errors = 0
    
    logger.info(f"🚀 이월상품 수집 시작: {len(outlet_keywords)}개 키워드")
    
    for keyword in outlet_keywords:
        try:
            # 네이버 쇼핑 검색
            products = crawler.search(keyword, limit=100, sort='dsc')  # 가격 높은순 (할인 전)
            
            logger.info(f"'{keyword}': {len(products)}개 검색됨")
            
            # 할인율 30% 이상만 필터링
            outlet_products = [p for p in products if p.get('discount_rate', 0) >= 30]
            
            logger.info(f"  → 할인율 30% 이상: {len(outlet_products)}개")
            
            # DB 저장
            for product_data in outlet_products:
                try:
                    # 브랜드 생성/조회
                    brand_name = product_data.get('brand', keyword.split()[0])
                    brand, _ = Brand.objects.get_or_create(
                        name=brand_name,
                        defaults={'slug': brand_name.lower().replace(' ', '-')}
                    )
                    
                    # 카테고리 매핑
                    category_slug = product_data.get('category', 'generic')
                    try:
                        category = Category.objects.get(slug=category_slug)
                    except Category.DoesNotExist:
                        category = Category.objects.get(slug='generic')
                    
                    # 모델 선택
                    if category_slug == 'down':
                        Model = DownProduct
                    elif category_slug == 'coat':
                        Model = CoatProduct
                    else:
                        Model = GenericProduct
                    
                    # 상품 ID (naver-productId)
                    product_id = f"naver-{product_data['product_id']}"
                    
                    # DB 데이터 준비
                    db_data = {
                        'brand': brand,
                        'category': category,
                        'title': product_data['title'][:500],
                        'slug': product_data['title'][:100].lower().replace(' ', '-'),
                        'image_url': product_data.get('image_url', ''),
                        'price': product_data['price'],
                        'original_price': product_data.get('original_price', product_data['price']),
                        'discount_rate': product_data.get('discount_rate', 0),
                        'seller': product_data.get('seller', '')[:100],
                        'deeplink': product_data.get('product_url', ''),  # 구매 링크
                        'in_stock': True,
                        'score': float(product_data.get('score', 0.0)),
                        'source': 'naver',
                        'updated_at': timezone.now(),
                    }
                    
                    # Upsert
                    product, is_created = Model.objects.update_or_create(
                        id=product_id,
                        defaults=db_data
                    )
                    
                    if is_created:
                        total_created += 1
                        logger.info(f"  ✅ 신규: {product.title[:50]}")
                    else:
                        total_updated += 1
                        logger.info(f"  🔄 업데이트: {product.title[:50]}")
                        
                except Exception as e:
                    logger.error(f"  ❌ 저장 실패: {e}")
                    total_errors += 1
                    continue
            
        except Exception as e:
            logger.error(f"❌ '{keyword}' 검색 실패: {e}")
            continue
    
    logger.info(f"\n✨ 수집 완료!")
    logger.info(f"  신규 생성: {total_created}개")
    logger.info(f"  업데이트: {total_updated}개")
    logger.info(f"  에러: {total_errors}개")
    
    return {
        'created': total_created,
        'updated': total_updated,
        'errors': total_errors
    }


if __name__ == '__main__':
    result = collect_outlet_products()
    print(f"\n{'='*60}")
    print(f"수집 결과 요약")
    print(f"{'='*60}")
    print(f"신규 상품: {result['created']}개")
    print(f"업데이트: {result['updated']}개")
    print(f"에러: {result['errors']}개")
    print(f"{'='*60}")
