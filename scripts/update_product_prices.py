"""
실시간 가격 업데이트 스크립트
기존 상품들의 최신 가격 확인 및 업데이트
"""
import os
import sys
import django

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
django.setup()

from apps.products.models import GenericProduct, DownProduct, CoatProduct
from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler
from django.utils import timezone
import logging
import time

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def update_product_prices():
    """네이버 출처 상품들의 가격 실시간 업데이트"""
    
    crawler = NaverShoppingCrawler()
    
    # 네이버 출처 상품만 조회
    models = [GenericProduct, DownProduct, CoatProduct]
    all_products = []
    
    for Model in models:
        products = Model.objects.filter(source='naver', in_stock=True)
        all_products.extend(products)
    
    logger.info(f"🔄 가격 업데이트 시작: {len(all_products)}개 상품")
    
    updated_count = 0
    price_changed = 0
    out_of_stock = 0
    errors = 0
    
    for product in all_products:
        try:
            # 상품 ID에서 네이버 productId 추출
            naver_product_id = product.id.replace('naver-', '')
            
            # 브랜드명으로 재검색 (상품명 일부 포함)
            search_query = f"{product.brand.name} {product.title.split()[0]}"
            
            # API 호출 (1초당 10건 제한 고려)
            time.sleep(0.1)  # 100ms 대기
            
            results = crawler.search(search_query, limit=5)
            
            # 동일 상품 찾기 (product_id 일치)
            found = False
            for result in results:
                if result['product_id'] == naver_product_id:
                    found = True
                    
                    # 가격 변동 확인
                    old_price = product.price
                    new_price = result['price']
                    
                    if old_price != new_price:
                        price_changed += 1
                        logger.info(f"💰 가격 변동: {product.title[:40]}")
                        logger.info(f"   {old_price:,}원 → {new_price:,}원")
                    
                    # 가격 업데이트
                    product.price = new_price
                    product.original_price = result.get('original_price', new_price)
                    product.discount_rate = result.get('discount_rate', 0)
                    product.updated_at = timezone.now()
                    product.save()
                    
                    updated_count += 1
                    break
            
            if not found:
                # 검색 결과에 없음 = 품절 가능성
                logger.warning(f"⚠️  검색 결과 없음 (품절?): {product.title[:40]}")
                product.in_stock = False
                product.save()
                out_of_stock += 1
                
        except Exception as e:
            logger.error(f"❌ 업데이트 실패: {product.title[:40]} - {e}")
            errors += 1
            continue
    
    logger.info(f"\n✨ 가격 업데이트 완료!")
    logger.info(f"  업데이트: {updated_count}개")
    logger.info(f"  가격 변동: {price_changed}개")
    logger.info(f"  품절 처리: {out_of_stock}개")
    logger.info(f"  에러: {errors}개")
    
    return {
        'updated': updated_count,
        'price_changed': price_changed,
        'out_of_stock': out_of_stock,
        'errors': errors
    }


if __name__ == '__main__':
    result = update_product_prices()
    print(f"\n{'='*60}")
    print(f"가격 업데이트 결과")
    print(f"{'='*60}")
    print(f"업데이트: {result['updated']}개")
    print(f"가격 변동: {result['price_changed']}개")
    print(f"품절 처리: {result['out_of_stock']}개")
    print(f"에러: {result['errors']}개")
    print(f"{'='*60}")
