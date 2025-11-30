"""
SEO Services
메타 태그, 구조화 데이터, URL 최적화
"""
from typing import Dict, Any, List, Optional
from django.conf import settings
from django.urls import reverse
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class SEOMetaGenerator:
    """SEO 메타 태그 생성기
    
    Features:
        - Open Graph 태그
        - Twitter Card 태그
        - Canonical URL
        - 동적 meta description
        - 키워드 생성
    """
    
    def __init__(self, request=None):
        self.request = request
        self.site_name = "E-wall"
        self.site_description = "아웃도어 브랜드 이월 상품 최저가 검색"
        self.base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'https://ewall.com'
    
    def generate_landing_page_meta(
        self,
        brand_name: str,
        category_name: str,
        products: List[Any] = None,
        custom_description: str = None
    ) -> Dict[str, Any]:
        """랜딩 페이지 메타 태그 생성
        
        Args:
            brand_name: 브랜드명
            category_name: 카테고리명
            products: 상품 리스트 (할인율 계산용)
            custom_description: 커스텀 설명
        
        Returns:
            메타 태그 딕셔너리
        """
        # 최대 할인율 계산
        max_discount = 0
        if products:
            discounts = [float(p.discount_rate) for p in products if hasattr(p, 'discount_rate')]
            max_discount = max(discounts) if discounts else 0
        
        # 기본 제목
        title = f"{brand_name} {category_name} 이월 특가"
        if max_discount > 0:
            title += f" 최대 {int(max_discount)}% 할인"
        
        # 설명
        if custom_description:
            description = custom_description
        else:
            description = f"{brand_name} {category_name} 최저가 검색. "
            if max_discount > 0:
                description += f"최대 {int(max_discount)}% 할인 상품 모음. "
            description += "다양한 필터로 맞춤 검색 가능."
        
        # 키워드
        keywords = [
            brand_name,
            category_name,
            "이월",
            "특가",
            "할인",
            "최저가",
            "아웃도어",
        ]
        
        # Canonical URL
        canonical_url = f"{self.base_url}/{self._slugify(brand_name)}/{self._slugify(category_name)}/"
        
        # OG 이미지 (첫 번째 상품 이미지 또는 기본 이미지)
        og_image = self.base_url + "/static/images/og-default.jpg"
        if products and len(products) > 0 and hasattr(products[0], 'image_url'):
            og_image = products[0].image_url or og_image
        
        return {
            'title': title,
            'description': description[:160],  # 160자 제한
            'keywords': ', '.join(keywords),
            'canonical_url': canonical_url,
            'og': {
                'title': title,
                'description': description[:200],
                'type': 'website',
                'url': canonical_url,
                'image': og_image,
                'site_name': self.site_name,
            },
            'twitter': {
                'card': 'summary_large_image',
                'title': title,
                'description': description[:200],
                'image': og_image,
            }
        }
    
    def generate_product_detail_meta(
        self,
        product: Any,
        brand_name: str = None,
        category_name: str = None
    ) -> Dict[str, Any]:
        """상품 상세 페이지 메타 태그 생성
        
        Args:
            product: 상품 객체
            brand_name: 브랜드명 (선택)
            category_name: 카테고리명 (선택)
        
        Returns:
            메타 태그 딕셔너리
        """
        brand = brand_name or (product.brand.name if hasattr(product, 'brand') else '브랜드')
        category = category_name or (product.category.name if hasattr(product, 'category') else '카테고리')
        
        # 제목 (70자 제한)
        title = f"{product.title[:50]} - {brand} {category}"
        
        # 설명
        description = f"{product.title}. "
        if hasattr(product, 'price'):
            description += f"{int(product.price):,}원"
            if hasattr(product, 'discount_rate') and product.discount_rate > 0:
                description += f" ({int(product.discount_rate)}% 할인)"
        description += f". {brand} {category} 최저가 검색."
        
        # 키워드
        keywords = [
            brand,
            category,
            product.title.split()[0] if product.title else '',
            "이월",
            "특가",
        ]
        
        # Canonical URL
        canonical_url = f"{self.base_url}/products/{product.id}/"
        
        # OG 이미지
        og_image = getattr(product, 'image_url', None) or f"{self.base_url}/static/images/og-default.jpg"
        
        return {
            'title': title,
            'description': description[:160],
            'keywords': ', '.join(keywords),
            'canonical_url': canonical_url,
            'og': {
                'title': title,
                'description': description[:200],
                'type': 'product',
                'url': canonical_url,
                'image': og_image,
                'site_name': self.site_name,
            },
            'twitter': {
                'card': 'summary_large_image',
                'title': title,
                'description': description[:200],
                'image': og_image,
            }
        }
    
    def generate_home_meta(self) -> Dict[str, Any]:
        """홈페이지 메타 태그 생성"""
        title = f"{self.site_name} - 아웃도어 이월 상품 최저가 검색"
        description = "노스페이스, 파타고니아, 아크테릭스 등 아웃도어 브랜드 이월 상품을 한 곳에서 비교하세요. 최대 70% 할인!"
        
        return {
            'title': title,
            'description': description,
            'keywords': 'E-wall, 이월, 아웃도어, 특가, 할인, 노스페이스, 파타고니아',
            'canonical_url': self.base_url + '/',
            'og': {
                'title': title,
                'description': description,
                'type': 'website',
                'url': self.base_url + '/',
                'image': self.base_url + '/static/images/og-home.jpg',
                'site_name': self.site_name,
            },
            'twitter': {
                'card': 'summary_large_image',
                'title': title,
                'description': description,
                'image': self.base_url + '/static/images/og-home.jpg',
            }
        }
    
    def _slugify(self, text: str) -> str:
        """간단한 slug 변환 (한글 지원)"""
        # 실제로는 Brand/Category 모델의 slug 필드 사용
        return text.lower().replace(' ', '-')


class StructuredDataGenerator:
    """Schema.org 구조화 데이터 생성기
    
    Features:
        - Product schema
        - BreadcrumbList schema
        - Organization schema
        - CollectionPage schema
        - Offer schema
    """
    
    def __init__(self, request=None):
        self.request = request
        self.base_url = settings.BASE_URL if hasattr(settings, 'BASE_URL') else 'https://ewall.com'
    
    def generate_product_schema(self, product: Any, brand: Any = None, category: Any = None) -> Dict[str, Any]:
        """Product schema.org 데이터 생성
        
        Args:
            product: 상품 객체
            brand: 브랜드 객체 (선택)
            category: 카테고리 객체 (선택)
        
        Returns:
            JSON-LD 데이터
        """
        brand_obj = brand or getattr(product, 'brand', None)
        category_obj = category or getattr(product, 'category', None)
        
        schema = {
            "@context": "https://schema.org",
            "@type": "Product",
            "name": product.title,
            "description": product.title,
            "image": getattr(product, 'image_url', ''),
            "brand": {
                "@type": "Brand",
                "name": brand_obj.name if brand_obj else "브랜드"
            },
            "category": category_obj.name if category_obj else "카테고리",
            "offers": {
                "@type": "Offer",
                "url": f"{self.base_url}/products/{product.id}/",
                "priceCurrency": "KRW",
                "price": str(float(product.price)) if hasattr(product, 'price') else "0",
                "availability": "https://schema.org/InStock" if getattr(product, 'in_stock', False) else "https://schema.org/OutOfStock",
                "priceValidUntil": self._get_price_valid_until(),
            }
        }
        
        # 리뷰 정보 (선택사항)
        if hasattr(product, 'rating') and product.rating:
            schema["aggregateRating"] = {
                "@type": "AggregateRating",
                "ratingValue": str(product.rating),
                "reviewCount": str(getattr(product, 'review_count', 0))
            }
        
        return schema
    
    def generate_collection_page_schema(
        self,
        brand_name: str,
        category_name: str,
        products: List[Any] = None
    ) -> Dict[str, Any]:
        """CollectionPage schema.org 데이터 생성
        
        Args:
            brand_name: 브랜드명
            category_name: 카테고리명
            products: 상품 리스트 (선택)
        
        Returns:
            JSON-LD 데이터
        """
        url = f"{self.base_url}/{self._slugify(brand_name)}/{self._slugify(category_name)}/"
        
        schema = {
            "@context": "https://schema.org",
            "@type": "CollectionPage",
            "name": f"{brand_name} {category_name} 이월 특가",
            "description": f"{brand_name} {category_name} 최대 할인 모음",
            "url": url,
        }
        
        # 상품 목록 추가 (선택사항)
        if products:
            schema["mainEntity"] = {
                "@type": "ItemList",
                "itemListElement": [
                    {
                        "@type": "ListItem",
                        "position": i + 1,
                        "item": self.generate_product_schema(product)
                    }
                    for i, product in enumerate(products[:10])  # 최대 10개
                ]
            }
        
        return schema
    
    def generate_breadcrumb_schema(self, items: List[Dict[str, str]]) -> Dict[str, Any]:
        """BreadcrumbList schema.org 데이터 생성
        
        Args:
            items: [{"name": "홈", "url": "/"}, {"name": "브랜드", "url": "/brand/"}]
        
        Returns:
            JSON-LD 데이터
        """
        return {
            "@context": "https://schema.org",
            "@type": "BreadcrumbList",
            "itemListElement": [
                {
                    "@type": "ListItem",
                    "position": i + 1,
                    "name": item["name"],
                    "item": self.base_url + item["url"]
                }
                for i, item in enumerate(items)
            ]
        }
    
    def generate_organization_schema(self) -> Dict[str, Any]:
        """Organization schema.org 데이터 생성"""
        return {
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": "E-wall",
            "url": self.base_url,
            "logo": f"{self.base_url}/static/images/logo.png",
            "description": "아웃도어 브랜드 이월 상품 최저가 검색 플랫폼",
            "sameAs": [
                # 소셜 미디어 링크 (실제 링크로 교체)
                "https://www.facebook.com/ewall",
                "https://www.instagram.com/ewall",
            ]
        }
    
    def _slugify(self, text: str) -> str:
        """간단한 slug 변환"""
        return text.lower().replace(' ', '-')
    
    def _get_price_valid_until(self) -> str:
        """가격 유효 기간 (30일)"""
        from datetime import datetime, timedelta
        valid_until = datetime.now() + timedelta(days=30)
        return valid_until.strftime('%Y-%m-%d')
