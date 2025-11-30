from django.apps import AppConfig
import logging

logger = logging.getLogger(__name__)


class ProductsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.products'
    verbose_name = '상품'
    
    def ready(self):
        """앱 초기화 시 실행"""
        import sys
        from django.conf import settings
        
        # 마이그레이션, 테스트, 관리 명령어 실행 시에는 스킵
        skip_commands = ['migrate', 'makemigrations', 'test', 'shell', 'createsuperuser']
        if any(cmd in sys.argv for cmd in skip_commands):
            return
        
        # runserver 명령어 실행 시에만 체크
        if 'runserver' in sys.argv:
            # 개발 환경에서만 실행
            if settings.DEBUG:
                # Django가 완전히 로드된 후 실행 (리로드 시 중복 방지)
                import os
                if os.environ.get('RUN_MAIN') == 'true':
                    self._check_and_generate_embeddings()
    
    def _check_and_generate_embeddings(self):
        """임베딩 누락 상품 체크 및 자동 생성"""
        try:
            from apps.products.models import GenericProduct
            from apps.recommendations.models import ImageEmbedding
            from threading import Thread
            
            # 전체 상품 수
            total_products = GenericProduct.objects.filter(in_stock=True).count()
            
            if total_products == 0:
                logger.info("📦 재고 있는 상품이 없습니다. 임베딩 체크를 건너뜁니다.")
                return
            
            # 임베딩 있는 상품 ID
            existing_embeddings = set(
                ImageEmbedding.objects.filter(model_version='resnet50')
                .values_list('product_id', flat=True)
            )
            
            # 임베딩 없는 상품들
            products_without_embedding = GenericProduct.objects.filter(
                in_stock=True
            ).exclude(
                id__in=existing_embeddings
            )
            
            missing_count = products_without_embedding.count()
            coverage = ((total_products - missing_count) / total_products * 100) if total_products > 0 else 0
            
            logger.info("=" * 60)
            logger.info("🎨 이미지 임베딩 상태 체크")
            logger.info("=" * 60)
            logger.info(f"총 상품:         {total_products:4}개")
            logger.info(f"임베딩 존재:     {total_products - missing_count:4}개")
            logger.info(f"임베딩 누락:     {missing_count:4}개")
            logger.info(f"커버리지:        {coverage:.1f}%")
            
            if missing_count > 0:
                logger.warning(f"⚠️  {missing_count}개 상품의 임베딩이 없습니다.")
                logger.info("🔧 백그라운드에서 임베딩 생성을 시작합니다...")
                
                # 백그라운드 스레드로 생성 (서버 시작 차단 방지)
                thread = Thread(
                    target=self._generate_embeddings_background,
                    args=(products_without_embedding[:50],),  # 최대 50개만
                    daemon=True
                )
                thread.start()
            else:
                logger.info("✅ 모든 상품에 임베딩이 존재합니다!")
            
            logger.info("=" * 60)
            
        except Exception as e:
            logger.error(f"❌ 임베딩 체크 중 오류: {e}")
    
    def _generate_embeddings_background(self, products):
        """백그라운드에서 임베딩 생성 (서버 시작 차단 방지)"""
        import time
        from apps.recommendations.services.image_embedding import ImageEmbeddingService
        from apps.recommendations.models import ImageEmbedding
        
        # 서버 완전히 시작될 때까지 대기
        time.sleep(3)
        
        logger.info(f"🎨 {products.count()}개 상품의 임베딩 생성을 시작합니다...")
        
        service = ImageEmbeddingService()
        success_count = 0
        fail_count = 0
        
        for idx, product in enumerate(products, 1):
            try:
                if not product.image_url:
                    logger.debug(f"[{idx}/{products.count()}] ⏭️  이미지 없음: {product.title[:40]}")
                    continue
                
                # 중복 체크 (혹시 이미 생성되었을 경우 스킵)
                if ImageEmbedding.objects.filter(product_id=str(product.id)).exists():
                    logger.debug(f"[{idx}/{products.count()}] ⏭️  이미 존재: {product.title[:40]}")
                    continue
                
                # 임베딩 생성
                embedding_vector = service.get_embedding_from_url(product.image_url)
                
                if embedding_vector is None:
                    logger.warning(f"[{idx}/{products.count()}] ❌ 생성 실패: {product.title[:40]}")
                    fail_count += 1
                    continue
                
                # DB 저장
                ImageEmbedding.objects.create(
                    product_id=str(product.id),
                    image_url=product.image_url,
                    embedding_vector=embedding_vector.tolist(),
                    model_version='resnet50'
                )
                
                success_count += 1
                logger.info(f"[{idx}/{products.count()}] ✅ 생성 완료: {product.title[:40]}")
                
                # API 부하 방지 (0.5초 대기)
                time.sleep(0.5)
                
            except Exception as e:
                logger.error(f"[{idx}/{products.count()}] ❌ 오류: {product.title[:40]} - {e}")
                fail_count += 1
                continue
        
        logger.info("=" * 60)
        logger.info(f"✅ 임베딩 생성 완료: 성공 {success_count}개, 실패 {fail_count}개")
        logger.info("=" * 60)
