"""
Django management command: 이미지 임베딩 일괄 생성
"""
from django.core.management.base import BaseCommand
from apps.products.models import GenericProduct
from apps.recommendations.models import ImageEmbedding
from apps.recommendations.services.image_embedding import ImageEmbeddingService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '임베딩이 없는 상품들의 이미지 임베딩을 일괄 생성합니다'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            default=None,
            help='처리할 최대 상품 수 (기본: 전체)'
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='기존 임베딩도 다시 생성'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        force = options.get('force')
        
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('🎨 이미지 임베딩 일괄 생성 시작'))
        self.stdout.write("=" * 60)
        
        # 임베딩 서비스 초기화
        service = ImageEmbeddingService()
        
        # 처리할 상품 조회
        if force:
            # 전체 재생성
            products = GenericProduct.objects.filter(in_stock=True)
            if limit:
                products = products[:limit]
            self.stdout.write(f"🔄 전체 재생성 모드 (limit={limit or '전체'})")
        else:
            # 임베딩 없는 것만
            existing_product_ids = set(
                ImageEmbedding.objects.filter(model_version='resnet50')
                .values_list('product_id', flat=True)
            )
            products = GenericProduct.objects.filter(
                in_stock=True
            ).exclude(id__in=existing_product_ids)
            if limit:
                products = products[:limit]
            self.stdout.write(f"✨ 신규 생성 모드 (limit={limit or '전체'})")
        
        total = products.count()
        self.stdout.write(f"📊 처리 대상: {total}개 상품\n")
        
        # 통계
        stats = {
            'total': total,
            'created': 0,
            'updated': 0,
            'skipped': 0,
            'failed': 0,
        }
        
        # 각 상품 처리
        for idx, product in enumerate(products, 1):
            try:
                # 이미지 URL 체크
                if not product.image_url:
                    stats['skipped'] += 1
                    self.stdout.write(f"[{idx}/{total}] ⏭️  이미지 없음: {product.title[:40]}")
                    continue
                
                # 기존 임베딩 확인
                existing = ImageEmbedding.objects.filter(
                    product_id=str(product.id),
                    model_version='resnet50'
                ).first()
                
                if existing and not force:
                    stats['skipped'] += 1
                    self.stdout.write(f"[{idx}/{total}] ⏭️  이미 존재: {product.title[:40]}")
                    continue
                
                # 임베딩 생성
                embedding_vector = service.get_embedding_from_url(product.image_url)
                
                if embedding_vector is None:
                    stats['failed'] += 1
                    self.stdout.write(
                        self.style.WARNING(f"[{idx}/{total}] ❌ 생성 실패: {product.title[:40]}")
                    )
                    continue
                
                # DB 저장
                if existing and force:
                    existing.embedding_vector = embedding_vector.tolist()
                    existing.image_url = product.image_url
                    existing.save()
                    stats['updated'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"[{idx}/{total}] 🔄 업데이트: {product.title[:40]}")
                    )
                else:
                    ImageEmbedding.objects.create(
                        product_id=str(product.id),
                        image_url=product.image_url,
                        embedding_vector=embedding_vector.tolist(),
                        model_version='resnet50'
                    )
                    stats['created'] += 1
                    self.stdout.write(
                        self.style.SUCCESS(f"[{idx}/{total}] ✅ 생성: {product.title[:40]}")
                    )
                
            except Exception as e:
                stats['failed'] += 1
                self.stdout.write(
                    self.style.ERROR(f"[{idx}/{total}] ❌ 오류: {product.title[:40]} - {e}")
                )
                continue
        
        # 결과 출력
        self.stdout.write("\n" + "=" * 60)
        self.stdout.write(self.style.SUCCESS('📊 처리 결과'))
        self.stdout.write("=" * 60)
        self.stdout.write(f"총 처리:     {stats['total']:4}개")
        self.stdout.write(self.style.SUCCESS(f"생성 성공:   {stats['created']:4}개"))
        self.stdout.write(self.style.SUCCESS(f"업데이트:    {stats['updated']:4}개"))
        self.stdout.write(self.style.WARNING(f"건너뜀:      {stats['skipped']:4}개"))
        self.stdout.write(self.style.ERROR(f"실패:        {stats['failed']:4}개"))
        
        # 현재 전체 임베딩 수
        total_embeddings = ImageEmbedding.objects.filter(model_version='resnet50').count()
        total_products = GenericProduct.objects.filter(in_stock=True).count()
        coverage = (total_embeddings / total_products * 100) if total_products > 0 else 0
        
        self.stdout.write(f"\n현재 임베딩 커버리지: {total_embeddings}/{total_products} ({coverage:.1f}%)")
        self.stdout.write("=" * 60)
