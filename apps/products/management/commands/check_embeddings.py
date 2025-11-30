"""
Django management command: 임베딩 상태 체크
"""
from django.core.management.base import BaseCommand
from apps.products.models import GenericProduct
from apps.recommendations.models import ImageEmbedding


class Command(BaseCommand):
    help = '임베딩 상태를 확인합니다 (생성은 하지 않음)'

    def handle(self, *args, **options):
        # 전체 상품 수
        total_products = GenericProduct.objects.filter(in_stock=True).count()
        
        # 임베딩 있는 상품
        total_embeddings = ImageEmbedding.objects.filter(model_version='resnet50').count()
        
        # 임베딩 없는 상품들
        existing_product_ids = set(
            ImageEmbedding.objects.filter(model_version='resnet50')
            .values_list('product_id', flat=True)
        )
        
        products_without_embedding = GenericProduct.objects.filter(
            in_stock=True
        ).exclude(
            id__in=existing_product_ids
        )
        
        missing_count = products_without_embedding.count()
        coverage = ((total_embeddings / total_products * 100) if total_products > 0 else 0)
        
        # 결과 출력
        self.stdout.write("=" * 60)
        self.stdout.write(self.style.SUCCESS('🎨 이미지 임베딩 상태'))
        self.stdout.write("=" * 60)
        self.stdout.write(f"총 상품 (재고 있음):  {total_products:4}개")
        self.stdout.write(f"임베딩 존재:          {total_embeddings:4}개")
        self.stdout.write(f"임베딩 누락:          {missing_count:4}개")
        self.stdout.write(f"커버리지:             {coverage:.1f}%")
        self.stdout.write("=" * 60)
        
        if missing_count > 0:
            self.stdout.write("")
            self.stdout.write(self.style.WARNING(f"⚠️  {missing_count}개 상품의 임베딩이 없습니다."))
            self.stdout.write("")
            self.stdout.write("임베딩 생성 방법:")
            self.stdout.write(self.style.SUCCESS("  python manage.py generate_embeddings"))
            self.stdout.write("")
            
            # 누락된 상품 샘플 출력
            self.stdout.write("누락된 상품 샘플 (최대 10개):")
            for idx, product in enumerate(products_without_embedding[:10], 1):
                self.stdout.write(f"  {idx}. {product.title[:60]}")
        else:
            self.stdout.write("")
            self.stdout.write(self.style.SUCCESS("✅ 모든 상품에 임베딩이 존재합니다!"))
        
        self.stdout.write("=" * 60)
