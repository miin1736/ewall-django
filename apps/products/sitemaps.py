"""
Product Sitemap - 확장된 SEO 최적화
"""
from django.contrib.sitemaps import Sitemap
from django.utils import timezone
from apps.core.models import Brand, Category
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct
)


class LandingPageSitemap(Sitemap):
    """브랜드×카테고리 랜딩 페이지 사이트맵"""
    changefreq = "daily"
    priority = 0.8
    protocol = 'https'
    
    def items(self):
        """브랜드×카테고리 조합 생성"""
        brands = Brand.objects.all()
        categories = Category.objects.all()
        
        items = []
        for brand in brands:
            for category in categories:
                items.append({
                    'brand_slug': brand.slug,
                    'category_slug': category.slug,
                    'lastmod': timezone.now(),
                })
        
        return items
    
    def location(self, item):
        return f"/landing/{item['brand_slug']}/{item['category_slug']}/"
    
    def lastmod(self, item):
        return item['lastmod']


class ProductDetailSitemap(Sitemap):
    """개별 상품 상세 페이지 사이트맵"""
    changefreq = "weekly"
    priority = 0.6
    protocol = 'https'
    limit = 5000  # 한 사이트맵당 최대 5000개
    
    def items(self):
        """활성화된 상품만 포함 (모든 상품 모델)"""
        models = [DownProduct, SlacksProduct, JeansProduct,
                  CrewneckProduct, LongSleeveProduct, CoatProduct]
        
        all_products = []
        for model in models:
            products = model.objects.filter(
                in_stock=True
            ).select_related('brand', 'category')
            all_products.extend(list(products))
        
        # 업데이트 시간순 정렬
        all_products.sort(key=lambda x: x.updated_at, reverse=True)
        return all_products[:5000]
    
    def location(self, obj):
        return f"/products/{obj.id}/"
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def priority(self, obj):
        """할인율이 높은 상품은 우선순위 높게"""
        if obj.discount_rate > 50:
            return 0.9
        elif obj.discount_rate > 30:
            return 0.7
        return 0.6


class ProductImageSitemap(Sitemap):
    """상품 이미지 사이트맵 (Google Image Search)"""
    changefreq = "monthly"
    priority = 0.5
    protocol = 'https'
    limit = 1000
    
    def items(self):
        """이미지가 있는 상품만"""
        models = [DownProduct, SlacksProduct, JeansProduct,
                  CrewneckProduct, LongSleeveProduct, CoatProduct]
        
        all_products = []
        for model in models:
            products = model.objects.filter(
                in_stock=True,
                image_url__isnull=False
            ).exclude(image_url='').select_related('brand', 'category')
            all_products.extend(list(products))
        
        return all_products[:1000]
    
    def location(self, obj):
        return f"/products/{obj.id}/"
    
    def lastmod(self, obj):
        return obj.updated_at
