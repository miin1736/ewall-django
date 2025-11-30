"""
샘플 데이터 생성 커맨드
Usage: python manage.py create_sample_data --count 10 --clear
"""
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from apps.core.models import Brand, Category
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct
)
from decimal import Decimal
import random


class Command(BaseCommand):
    help = '샘플 데이터 생성 (브랜드, 카테고리, 상품)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=10,
            help='카테고리별 생성할 상품 수 (기본: 10)'
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='기존 데이터 삭제 후 생성'
        )

    def handle(self, *args, **options):
        count = options['count']
        clear_data = options['clear']
        
        if clear_data:
            self.stdout.write(self.style.WARNING('\n기존 데이터 삭제 중...'))
            DownProduct.objects.all().delete()
            SlacksProduct.objects.all().delete()
            JeansProduct.objects.all().delete()
            CrewneckProduct.objects.all().delete()
            LongSleeveProduct.objects.all().delete()
            CoatProduct.objects.all().delete()
            Brand.objects.all().delete()
            Category.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('✓ 기존 데이터 삭제 완료'))
        
        self.stdout.write(self.style.SUCCESS('\n=== 샘플 데이터 생성 시작 ===\n'))
        
        # 1. 브랜드 생성
        self.stdout.write('1. 브랜드 생성 중...')
        brands = self._create_brands()
        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(brands)}개 브랜드 생성 완료'))
        
        # 2. 카테고리 생성
        self.stdout.write('2. 카테고리 생성 중...')
        categories = self._create_categories()
        self.stdout.write(self.style.SUCCESS(f'   ✓ {len(categories)}개 카테고리 생성 완료'))
        
        # 3. 상품 생성
        self.stdout.write(f'3. 상품 생성 중... (카테고리당 {count}개)')
        total = self._create_all_products(brands, categories, count)
        self.stdout.write(self.style.SUCCESS(f'   ✓ 총 {total}개 상품 생성 완료'))
        
        # 4. 통계 출력
        self._print_statistics()

    def _create_brands(self):
        """브랜드 생성"""
        brands_data = [
            {'name': '노스페이스', 'slug': 'the-north-face'},
            {'name': '파타고니아', 'slug': 'patagonia'},
            {'name': '마무트', 'slug': 'mammut'},
            {'name': '아크테릭스', 'slug': 'arcteryx'},
            {'name': '블랙야크', 'slug': 'blackyak'},
            {'name': '네파', 'slug': 'nepa'},
            {'name': '코오롱스포츠', 'slug': 'kolon-sport'},
            {'name': 'K2', 'slug': 'k2'},
        ]
        
        brands = []
        for data in brands_data:
            brand, _ = Brand.objects.get_or_create(**data)
            brands.append(brand)
        return brands

    def _create_categories(self):
        """카테고리 생성"""
        categories_data = [
            {'name': '다운', 'slug': 'down'},
            {'name': '슬랙스', 'slug': 'slacks'},
            {'name': '청바지', 'slug': 'jeans'},
            {'name': '크루넥', 'slug': 'crewneck'},
            {'name': '긴팔', 'slug': 'long-sleeve'},
            {'name': '코트', 'slug': 'coat'},
        ]
        
        categories = {}
        for data in categories_data:
            category, _ = Category.objects.get_or_create(**data)
            categories[data['slug']] = category
        return categories

    def _create_all_products(self, brands, categories, count):
        """모든 카테고리의 상품 생성"""
        total = 0
        total += self._create_down_products(brands, categories['down'], count)
        total += self._create_slacks_products(brands, categories['slacks'], count)
        total += self._create_jeans_products(brands, categories['jeans'], count)
        total += self._create_crewneck_products(brands, categories['crewneck'], count)
        total += self._create_longsleeve_products(brands, categories['long-sleeve'], count)
        total += self._create_coat_products(brands, categories['coat'], count)
        return total

    def _create_down_products(self, brands, category, count):
        """다운 상품 생성"""
        for i in range(count):
            brand = random.choice(brands)
            price = random.randint(150000, 500000)
            discount_rate = random.choice([10, 15, 20, 25, 30, 35, 40, 45, 50])
            product_id = f'DOWN-{brand.slug.upper()}-{i+1:03d}'
            
            DownProduct.objects.get_or_create(
                id=product_id,
                defaults={
                    'brand': brand,
                    'category': category,
                    'title': f'{brand.name} {random.choice(["경량", "프리미엄", "익스트림", "클래식"])} 다운 재킷 {i+1}',
                    'slug': slugify(f'{brand.slug}-down-jacket-{i+1}'),
                    'image_url': f'https://picsum.photos/seed/{product_id}/800/800',
                    'price': Decimal(price),
                    'original_price': Decimal(price),
                    'discount_rate': Decimal(discount_rate),
                    'seller': random.choice(['무신사', '29CM', 'SSF샵', 'W컨셉']),
                    'deeplink': f'https://example.com/products/{product_id}',
                    'in_stock': random.choice([True, True, True, False]),
                    'source': 'sample_data',
                    'down_type': random.choice(['goose', 'duck', 'synthetic']),
                    'down_ratio': random.choice(['90/10', '80/20', '70/30']),
                    'fill_power': random.choice([550, 600, 650, 700, 750, 800]),
                    'hood': random.choice([True, False]),
                    'fit': random.choice(['slim', 'regular', 'relaxed', 'oversized']),
                    'shell': random.choice(['nylon', 'polyester', 'gore-tex']),
                }
            )
        return count

    def _create_slacks_products(self, brands, category, count):
        """슬랙스 상품 생성"""
        for i in range(count):
            brand = random.choice(brands)
            price = random.randint(50000, 200000)
            discount_rate = random.choice([10, 15, 20, 25, 30, 35, 40])
            product_id = f'SLACKS-{brand.slug.upper()}-{i+1:03d}'
            
            SlacksProduct.objects.get_or_create(
                id=product_id,
                defaults={
                    'brand': brand,
                    'category': category,
                    'title': f'{brand.name} {random.choice(["테이퍼드", "와이드", "슬림", "클래식"])} 슬랙스 {i+1}',
                    'slug': slugify(f'{brand.slug}-slacks-{i+1}'),
                    'image_url': f'https://picsum.photos/seed/{product_id}/800/800',
                    'price': Decimal(price),
                    'original_price': Decimal(price),
                    'discount_rate': Decimal(discount_rate),
                    'seller': random.choice(['무신사', '29CM', 'SSF샵', 'W컨셉']),
                    'deeplink': f'https://example.com/products/{product_id}',
                    'in_stock': random.choice([True, True, True, False]),
                    'source': 'sample_data',
                    'waist_type': random.choice(['high', 'mid', 'low']),
                    'leg_opening': random.choice(['tapered', 'straight', 'wide']),
                    'stretch': random.choice([True, False]),
                    'pleats': random.choice(['single', 'double', 'none']),
                    'fit': random.choice(['slim', 'regular', 'relaxed']),
                    'shell': random.choice(['cotton', 'wool', 'polyester']),
                }
            )
        return count

    def _create_jeans_products(self, brands, category, count):
        """청바지 상품 생성"""
        for i in range(count):
            brand = random.choice(brands)
            price = random.randint(40000, 180000)
            discount_rate = random.choice([10, 15, 20, 25, 30, 35])
            product_id = f'JEANS-{brand.slug.upper()}-{i+1:03d}'
            
            JeansProduct.objects.get_or_create(
                id=product_id,
                defaults={
                    'brand': brand,
                    'category': category,
                    'title': f'{brand.name} {random.choice(["스키니", "레귤러", "와이드", "부츠컷"])} 청바지 {i+1}',
                    'slug': slugify(f'{brand.slug}-jeans-{i+1}'),
                    'image_url': f'https://picsum.photos/seed/{product_id}/800/800',
                    'price': Decimal(price),
                    'original_price': Decimal(price),
                    'discount_rate': Decimal(discount_rate),
                    'seller': random.choice(['무신사', '29CM', 'SSF샵', 'W컨셉']),
                    'deeplink': f'https://example.com/products/{product_id}',
                    'in_stock': random.choice([True, True, True, False]),
                    'source': 'sample_data',
                    'wash': random.choice(['light', 'medium', 'dark', 'black']),
                    'cut': random.choice(['skinny', 'slim', 'straight', 'bootcut', 'wide']),
                    'rise': random.choice(['low', 'mid', 'high']),
                    'stretch': random.choice([True, False]),
                    'distressed': random.choice([True, False]),
                }
            )
        return count

    def _create_crewneck_products(self, brands, category, count):
        """크루넥 상품 생성"""
        for i in range(count):
            brand = random.choice(brands)
            price = random.randint(30000, 120000)
            discount_rate = random.choice([10, 15, 20, 25, 30])
            product_id = f'CREW-{brand.slug.upper()}-{i+1:03d}'
            
            CrewneckProduct.objects.get_or_create(
                id=product_id,
                defaults={
                    'brand': brand,
                    'category': category,
                    'title': f'{brand.name} {random.choice(["베이직", "오버사이즈", "크롭", "루즈핏"])} 크루넥 {i+1}',
                    'slug': slugify(f'{brand.slug}-crewneck-{i+1}'),
                    'image_url': f'https://picsum.photos/seed/{product_id}/800/800',
                    'price': Decimal(price),
                    'original_price': Decimal(price),
                    'discount_rate': Decimal(discount_rate),
                    'seller': random.choice(['무신사', '29CM', 'SSF샵', 'W컨셉']),
                    'deeplink': f'https://example.com/products/{product_id}',
                    'in_stock': random.choice([True, True, True, False]),
                    'source': 'sample_data',
                    'neckline': random.choice(['crew', 'mock', 'v-neck', 'henley']),
                    'sleeve_length': random.choice(['short', 'long']),
                    'pattern': random.choice(['solid', 'stripe', 'graphic']),
                    'fit': random.choice(['slim', 'regular', 'oversized']),
                    'shell': random.choice(['cotton', 'fleece', 'wool', 'polyester']),
                }
            )
        return count

    def _create_longsleeve_products(self, brands, category, count):
        """긴팔 상품 생성"""
        for i in range(count):
            brand = random.choice(brands)
            price = random.randint(25000, 100000)
            discount_rate = random.choice([10, 15, 20, 25, 30])
            product_id = f'LONG-{brand.slug.upper()}-{i+1:03d}'
            
            LongSleeveProduct.objects.get_or_create(
                id=product_id,
                defaults={
                    'brand': brand,
                    'category': category,
                    'title': f'{brand.name} {random.choice(["베이직", "스트라이프", "프린트", "무지"])} 긴팔 티셔츠 {i+1}',
                    'slug': slugify(f'{brand.slug}-longsleeve-{i+1}'),
                    'image_url': f'https://picsum.photos/seed/{product_id}/800/800',
                    'price': Decimal(price),
                    'original_price': Decimal(price),
                    'discount_rate': Decimal(discount_rate),
                    'seller': random.choice(['무신사', '29CM', 'SSF샵', 'W컨셉']),
                    'deeplink': f'https://example.com/products/{product_id}',
                    'in_stock': random.choice([True, True, True, False]),
                    'source': 'sample_data',
                    'neckline': random.choice(['crew', 'v-neck', 'henley']),
                    'sleeve_type': random.choice(['raglan', 'set-in']),
                    'layering': random.choice([True, False]),
                    'fit': random.choice(['slim', 'regular', 'oversized']),
                    'shell': random.choice(['cotton', 'polyester', 'modal']),
                }
            )
        return count

    def _create_coat_products(self, brands, category, count):
        """코트 상품 생성"""
        for i in range(count):
            brand = random.choice(brands)
            price = random.randint(200000, 600000)
            discount_rate = random.choice([15, 20, 25, 30, 35, 40, 45])
            product_id = f'COAT-{brand.slug.upper()}-{i+1:03d}'
            
            CoatProduct.objects.get_or_create(
                id=product_id,
                defaults={
                    'brand': brand,
                    'category': category,
                    'title': f'{brand.name} {random.choice(["울", "캐시미어", "트렌치", "피코트"])} 코트 {i+1}',
                    'slug': slugify(f'{brand.slug}-coat-{i+1}'),
                    'image_url': f'https://picsum.photos/seed/{product_id}/800/800',
                    'price': Decimal(price),
                    'original_price': Decimal(price),
                    'discount_rate': Decimal(discount_rate),
                    'seller': random.choice(['무신사', '29CM', 'SSF샵', 'W컨셉']),
                    'deeplink': f'https://example.com/products/{product_id}',
                    'in_stock': random.choice([True, True, True, False]),
                    'source': 'sample_data',
                    'length': random.choice(['short', 'mid', 'long']),
                    'closure': random.choice(['button', 'zip', 'belt']),
                    'lining': random.choice(['full', 'half', 'none']),
                    'hood': random.choice([True, False]),
                    'fit': random.choice(['slim', 'regular', 'oversized']),
                    'shell': random.choice(['wool', 'cashmere', 'polyester']),
                }
            )
        return count

    def _print_statistics(self):
        """통계 출력"""
        self.stdout.write(self.style.SUCCESS('\n=== 생성 완료 ==='))
        self.stdout.write(f'브랜드: {Brand.objects.count()}개')
        self.stdout.write(f'카테고리: {Category.objects.count()}개')
        self.stdout.write(f'다운: {DownProduct.objects.count()}개')
        self.stdout.write(f'슬랙스: {SlacksProduct.objects.count()}개')
        self.stdout.write(f'청바지: {JeansProduct.objects.count()}개')
        self.stdout.write(f'크루넥: {CrewneckProduct.objects.count()}개')
        self.stdout.write(f'긴팔: {LongSleeveProduct.objects.count()}개')
        self.stdout.write(f'코트: {CoatProduct.objects.count()}개')
        
        total = (
            DownProduct.objects.count() +
            SlacksProduct.objects.count() +
            JeansProduct.objects.count() +
            CrewneckProduct.objects.count() +
            LongSleeveProduct.objects.count() +
            CoatProduct.objects.count()
        )
        self.stdout.write(f'\n총 상품: {total}개')
        self.stdout.write(self.style.SUCCESS('\n테스트 URL:'))
        self.stdout.write('http://127.0.0.1:8000/')
        self.stdout.write('http://127.0.0.1:8000/the-north-face/down/')
        self.stdout.write('http://127.0.0.1:8000/admin/')
