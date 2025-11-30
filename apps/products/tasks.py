"""
Product sync and data pipeline tasks
네이버 쇼핑 API 기반 자동화 시스템
"""
from celery import shared_task
from django.utils import timezone
from django.db import transaction
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def sync_naver_outlet_products(self):
    """네이버 쇼핑 이월상품 자동 동기화
    
    실행 주기: 6시간마다 (Celery Beat)
    
    Steps:
        1. 네이버 쇼핑 API로 이월상품 검색
        2. 브랜드별 데이터 수집
        3. 데이터 정규화 및 검증
        4. GenericProduct에 upsert
        5. 품절 상품 처리
    """
    try:
        from scripts.advanced_naver_outlet_loader import (
            NaverShoppingCrawler,
            BRAND_SEARCH_KEYWORDS
        )
        from apps.products.models import GenericProduct
        from apps.core.models import Brand, Category
        from django.utils.text import slugify
        
        logger.info("🚀 Starting Naver Shopping outlet products sync")
        
        crawler = NaverShoppingCrawler()
        
        total_searched = 0
        total_created = 0
        total_updated = 0
        total_errors = 0
        
        # 기타 카테고리 가져오기
        try:
            generic_category = Category.objects.get(slug='generic')
        except Category.DoesNotExist:
            generic_category, _ = Category.objects.get_or_create(
                slug='generic',
                defaults={'name': '기타', 'category_type': 'clothing'}
            )
        
        # 각 브랜드별 이월상품 검색
        for brand_kr, keywords in BRAND_SEARCH_KEYWORDS.items():
            for keyword in keywords:
                try:
                    query = f"{brand_kr} {keyword}"
                    logger.info(f"🔍 Searching: {query}")
                    
                    # 네이버 쇼핑 API 검색
                    products = crawler.search_products(query, display=100)
                    total_searched += len(products)
                    
                    # 각 상품 처리
                    for raw_product in products:
                        try:
                            # 데이터 정규화
                            normalized = crawler.normalize_product(raw_product)
                            
                            # 데이터 검증
                            if not crawler.validate_product(normalized):
                                continue
                            
                            # 브랜드 매핑
                            brand_name_kr = normalized.get('brand', brand_kr)
                            brand_slug = crawler.get_brand_slug(brand_name_kr)
                            
                            # 브랜드 조회/생성
                            brand, _ = Brand.objects.get_or_create(
                                slug=brand_slug,
                                defaults={
                                    'name': brand_name_kr,
                                    'logo_url': '',
                                    'description': ''
                                }
                            )
                            
                            # 카테고리 매핑
                            category_name = normalized.get('category', '기타')
                            category = crawler.get_or_create_category(category_name)
                            if not category:
                                category = generic_category
                            
                            # 고유 slug 생성 (제목 + product_id)
                            product_id = normalized['product_id']
                            title = normalized['title']
                            title_slug = slugify(title[:50])
                            unique_slug = f"{title_slug}-{product_id}"
                            
                            # DB 데이터 준비
                            db_data = {
                                'brand': brand,
                                'category': category,
                                'title': title[:500],
                                'slug': unique_slug[:200],
                                'image_url': normalized.get('image_url', ''),
                                'price': normalized['price'],
                                'original_price': normalized.get('original_price', normalized['price']),
                                'discount_rate': normalized.get('discount_rate', 0),
                                'seller': normalized.get('seller', '')[:100],
                                'deeplink': normalized.get('deeplink', ''),
                                'in_stock': True,
                                'score': 0,
                                'source': 'naver_shopping',
                                'updated_at': timezone.now(),
                            }
                            
                            # Upsert
                            product, is_created = GenericProduct.objects.update_or_create(
                                id=product_id,
                                defaults=db_data
                            )
                            
                            if is_created:
                                total_created += 1
                                logger.debug(f"✅ Created: {title[:50]}")
                                
                                # 새 상품: 이미지 임베딩 생성 (백그라운드)
                                try:
                                    generate_image_embedding.delay(
                                        product_id=str(product.id),
                                        image_url=product.image_url
                                    )
                                except Exception as emb_error:
                                    logger.warning(f"⚠️ Failed to queue embedding for {product_id}: {emb_error}")
                            else:
                                total_updated += 1
                                logger.debug(f"🔄 Updated: {title[:50]}")
                                
                        except Exception as e:
                            logger.error(f"❌ Failed to process product: {e}")
                            total_errors += 1
                            continue
                    
                except Exception as e:
                    logger.error(f"❌ Search failed for '{query}': {e}")
                    continue
        
        # 오래된 상품 품절 처리 (7일 이상 업데이트 안 된 상품)
        from datetime import timedelta
        cutoff_date = timezone.now() - timedelta(days=7)
        outdated_count = GenericProduct.objects.filter(
            source='naver_shopping',
            updated_at__lt=cutoff_date,
            in_stock=True
        ).update(in_stock=False)
        
        result = {
            'searched': total_searched,
            'created': total_created,
            'updated': total_updated,
            'errors': total_errors,
            'outdated_marked': outdated_count,
            'timestamp': timezone.now().isoformat()
        }
        
        logger.info(
            f"✅ Naver Shopping sync complete: "
            f"searched={total_searched}, created={total_created}, "
            f"updated={total_updated}, errors={total_errors}, "
            f"outdated={outdated_count}"
        )
        
        return result
        
    except Exception as exc:
        logger.error(f"❌ Naver Shopping sync failed: {exc}")
        raise self.retry(exc=exc, countdown=600)  # 10분 후 재시도


@shared_task(bind=True)
def snapshot_prices(self):
    """모든 GenericProduct의 현재 가격을 PriceHistory에 스냅샷 저장
    
    실행 주기: 매일 자정 (Celery Beat)
    
    Steps:
        1. GenericProduct에서 in_stock=True 상품 조회
        2. 각 상품의 현재 price, original_price, discount_rate 저장
        3. 중복 방지: 오늘 이미 기록된 상품은 스킵
        4. 가격 하락 감지 및 Alert 트리거
    """
    try:
        from apps.products.models import GenericProduct, PriceHistory
        
        logger.info("📸 Starting daily price snapshot")
        
        # 재고 있는 상품만
        products = GenericProduct.objects.filter(in_stock=True)
        logger.info(f"Processing {products.count()} GenericProduct products")
        
        total_snapshots = 0
        skipped = 0
        errors = 0
        
        # 오늘 날짜 (자정 기준)
        today = timezone.now().date()
        
        for product in products:
            try:
                # 오늘 이미 기록했는지 확인
                existing = PriceHistory.objects.filter(
                    product_id=product.id,
                    recorded_at__date=today
                ).exists()
                
                if existing:
                    skipped += 1
                    continue
                
                # 가격 스냅샷 생성
                PriceHistory.objects.create(
                    product_id=product.id,
                    product_type='GenericProduct',
                    price=product.price,
                    original_price=product.original_price,
                    discount_rate=product.discount_rate
                )
                total_snapshots += 1
                
            except Exception as e:
                logger.error(f"Failed to snapshot {product.id}: {e}")
                errors += 1
                continue
        
        logger.info(
            f"✅ Price snapshot complete: "
            f"created={total_snapshots}, skipped={skipped}, errors={errors}"
        )
        
        return {
            'snapshots_created': total_snapshots,
            'skipped': skipped,
            'errors': errors,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"❌ Price snapshot failed: {exc}")
        raise exc


@shared_task(bind=True)
def cleanup_old_price_history(self, days_to_keep: int = 90):
    """오래된 가격 이력 정리
    
    실행 주기: 매주 일요일 새벽 3시
    
    Args:
        days_to_keep: 보관할 일수 (기본 90일)
    """
    try:
        from apps.products.models import PriceHistory
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_to_keep)
        
        deleted_count, _ = PriceHistory.objects.filter(
            recorded_at__lt=cutoff_date
        ).delete()
        
        logger.info(
            f"🧹 Cleaned up {deleted_count} old price history records "
            f"(older than {days_to_keep} days)"
        )
        
        return {
            'deleted': deleted_count,
            'cutoff_date': cutoff_date.isoformat()
        }
        
    except Exception as exc:
        logger.error(f"❌ Price history cleanup failed: {exc}")
        raise exc


@shared_task(bind=True)
def cleanup_outdated_products(self, days_threshold: int = 30):
    """30일 이상 업데이트되지 않은 상품 삭제
    
    실행 주기: 매월 1일
    
    Args:
        days_threshold: 삭제 기준 일수 (기본 30일)
    """
    try:
        from apps.products.models import GenericProduct
        from datetime import timedelta
        
        cutoff_date = timezone.now() - timedelta(days=days_threshold)
        
        deleted_count, _ = GenericProduct.objects.filter(
            updated_at__lt=cutoff_date,
            source='naver_shopping'
        ).delete()
        
        logger.info(
            f"🗑️  Deleted {deleted_count} outdated products "
            f"(not updated for {days_threshold} days)"
        )
        
        return {
            'deleted': deleted_count,
            'cutoff_date': cutoff_date.isoformat(),
            'days_threshold': days_threshold
        }
        
    except Exception as exc:
        logger.error(f"❌ Product cleanup failed: {exc}")
        raise exc


@shared_task(bind=True, max_retries=2)
def generate_image_embedding(self, product_id: str, image_url: str):
    """단일 상품의 이미지 임베딩 생성
    
    Args:
        product_id: 상품 ID
        image_url: 이미지 URL
    
    Returns:
        dict: 임베딩 생성 결과
    """
    try:
        from apps.recommendations.models import ImageEmbedding
        from apps.recommendations.services.image_embedding import ImageEmbeddingService
        
        # 이미 존재하는지 확인
        existing = ImageEmbedding.objects.filter(
            product_id=product_id,
            model_version='resnet50'
        ).exists()
        
        if existing:
            logger.debug(f"⏭️  Embedding already exists for {product_id}")
            return {'status': 'skipped', 'product_id': product_id}
        
        # 임베딩 생성
        service = ImageEmbeddingService()
        embedding_vector = service.get_embedding_from_url(image_url)
        
        if embedding_vector is None:
            logger.warning(f"⚠️ Failed to generate embedding for {product_id}")
            return {'status': 'failed', 'product_id': product_id}
        
        # DB 저장
        ImageEmbedding.objects.create(
            product_id=product_id,
            image_url=image_url,
            embedding_vector=embedding_vector.tolist(),
            model_version='resnet50'
        )
        
        logger.info(f"✅ Generated embedding for {product_id}")
        return {'status': 'created', 'product_id': product_id}
        
    except Exception as exc:
        logger.error(f"❌ Embedding generation failed for {product_id}: {exc}")
        raise self.retry(exc=exc, countdown=60)  # 1분 후 재시도


@shared_task(bind=True)
def batch_generate_embeddings(self, limit: int = 100):
    """임베딩이 없는 상품들의 임베딩 일괄 생성
    
    실행 주기: 매일 새벽 2시 (Celery Beat)
    
    Args:
        limit: 한 번에 처리할 최대 상품 수
    
    Returns:
        dict: 처리 결과 통계
    """
    try:
        from apps.products.models import GenericProduct
        from apps.recommendations.models import ImageEmbedding
        
        logger.info(f"🎨 Starting batch embedding generation (limit={limit})")
        
        # 임베딩 없는 상품 ID 조회
        existing_product_ids = set(
            ImageEmbedding.objects.filter(model_version='resnet50')
            .values_list('product_id', flat=True)
        )
        
        # 재고 있는 상품 중 임베딩 없는 것들
        products_without_embedding = GenericProduct.objects.filter(
            in_stock=True
        ).exclude(
            id__in=existing_product_ids
        )[:limit]
        
        total_queued = 0
        total_skipped = 0
        
        for product in products_without_embedding:
            if not product.image_url:
                total_skipped += 1
                continue
            
            # 비동기로 임베딩 생성 큐잉
            generate_image_embedding.delay(
                product_id=str(product.id),
                image_url=product.image_url
            )
            total_queued += 1
        
        logger.info(
            f"✅ Batch embedding generation queued: "
            f"queued={total_queued}, skipped={total_skipped}"
        )
        
        return {
            'queued': total_queued,
            'skipped': total_skipped,
            'timestamp': timezone.now().isoformat()
        }
        
    except Exception as exc:
        logger.error(f"❌ Batch embedding generation failed: {exc}")
        raise exc


