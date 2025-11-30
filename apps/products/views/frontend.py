"""
Frontend landing page view - SEO 최적화 + 페이지네이션
"""
from django.shortcuts import render, get_object_or_404
from django.core.cache import cache
from django.core.paginator import Paginator
from django.db.models import Q
from apps.core.models import Brand, Category
from apps.products.models import GenericProduct
from apps.core.services.seo import SEOMetaGenerator, StructuredDataGenerator
from itertools import chain
import json


def landing_page(request, brand_slug, category_slug):
    """브랜드×카테고리 랜딩 페이지 (SSR with SEO + Pagination)"""
    
    # 브랜드, 카테고리 조회
    brand = get_object_or_404(Brand, slug=brand_slug)
    category = get_object_or_404(Category, slug=category_slug)
    
    # GenericProduct로 통합
    queryset = GenericProduct.objects.filter(
        brand=brand,
        category=category,
        in_stock=True
    ).select_related('brand', 'category')
    
    # 검색 필터
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(
            Q(title__icontains=search_query)
        )
    
    # 가격 필터
    filters = {}
    price_min = request.GET.get('priceMin')
    price_max = request.GET.get('priceMax')
    if price_min:
        queryset = queryset.filter(price__gte=int(price_min))
        filters['priceMin'] = price_min
    if price_max:
        queryset = queryset.filter(price__lte=int(price_max))
        filters['priceMax'] = price_max
    
    # 할인율 필터
    discount_min = request.GET.get('discountMin')
    if discount_min:
        queryset = queryset.filter(discount_rate__gte=int(discount_min))
        filters['discountMin'] = discount_min
    
    # 정렬
    sort = request.GET.get('sort', 'discount')
    if sort == 'discount':
        queryset = queryset.order_by('-discount_rate')
    elif sort == 'price-low':
        queryset = queryset.order_by('price')
    elif sort == 'price-high':
        queryset = queryset.order_by('-price')
    elif sort == 'newest':
        queryset = queryset.order_by('-created_at')
    elif sort == 'popular':
        queryset = queryset.order_by('-discount_rate', '-created_at')
    
    # 페이지네이션
    page_size = int(request.GET.get('page_size', 20))
    page_number = int(request.GET.get('page', 1))
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)
    products = page_obj.object_list
    
    # 페이지 범위 계산 (최대 10개 페이지 번호 표시)
    page_range = []
    total_pages = paginator.num_pages
    
    if total_pages <= 10:
        page_range = range(1, total_pages + 1)
    else:
        if page_number <= 5:
            page_range = list(range(1, 8)) + ['...', total_pages]
        elif page_number >= total_pages - 4:
            page_range = [1, '...'] + list(range(total_pages - 6, total_pages + 1))
        else:
            page_range = [1, '...'] + list(range(page_number - 2, page_number + 3)) + ['...', total_pages]
    
    # SEO 메타 태그 생성
    seo_generator = SEOMetaGenerator(request)
    meta = seo_generator.generate_landing_page_meta(
        brand_name=brand.name,
        category_name=category.name,
        products=list(products)
    )
    
    # Schema.org 구조화 데이터 생성
    schema_generator = StructuredDataGenerator(request)
    schemas = [
        schema_generator.generate_collection_page_schema(
            brand_name=brand.name,
            category_name=category.name,
            products=list(products)[:10]  # 최대 10개
        ),
        schema_generator.generate_breadcrumb_schema([
            {'name': '홈', 'url': '/'},
            {'name': brand.name, 'url': f'/{brand_slug}/'},
            {'name': category.name, 'url': f'/{brand_slug}/{category_slug}/'}
        ]),
        schema_generator.generate_organization_schema()
    ]
    
    # 사이드바 데이터 (상품이 있는 브랜드/카테고리만)
    all_brands = Brand.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('brand_id', flat=True).distinct()
    ).order_by('name')
    categories = Category.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('category_id', flat=True).distinct()
    )
    
    context = {
        'brand': brand,
        'category': category,
        'products': products,
        'total': paginator.count,
        'page': page_number,
        'page_size': page_size,
        'total_pages': total_pages,
        'page_range': page_range,
        'sort': sort,
        'search_query': search_query,
        'filters': filters,
        'meta': meta,
        'schemas': [json.dumps(s, ensure_ascii=False, indent=2) for s in schemas],
        'view_type': 'landing',  # 브랜드+카테고리 조합
        'all_brands': all_brands,
        'categories': categories,
    }
    
    return render(request, 'frontend/landing.html', context)


def home(request):
    """홈 페이지 (무신사/다나와 스타일)"""
    from apps.core.models import Brand, Category
    from django.utils import timezone
    from datetime import timedelta
    from django.db.models import Count
    
    # 상품이 있는 브랜드 및 카테고리만
    all_brands = Brand.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('brand_id', flat=True).distinct()
    ).order_by('name')
    categories = Category.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('category_id', flat=True).distinct()
    )
    
    # 1. 최신 상품 (슬라이드쇼용) - 발매일 기준 최신 10개
    new_arrivals = GenericProduct.objects.filter(
        in_stock=True
    ).select_related('brand', 'category').order_by('-created_at')[:10]
    
    # 2. 일주일간 가장 많이 조회된 상품 (Click 모델 사용)
    from apps.analytics.models import Click
    week_ago = timezone.now() - timedelta(days=7)
    
    # 최근 일주일 클릭 통계
    popular_products_ids = Click.objects.filter(
        timestamp__gte=week_ago
    ).values('product_id').annotate(
        click_count=Count('id')
    ).order_by('-click_count')[:20]
    
    popular_products = []
    for item in popular_products_ids:
        product_id = item['product_id']
        try:
            product = GenericProduct.objects.select_related('brand', 'category').get(id=product_id, in_stock=True)
            popular_products.append(product)
        except GenericProduct.DoesNotExist:
            continue
    
    # 3. 30% 이상 할인 상품 (이월상품 기준)
    mega_deals = GenericProduct.objects.filter(
        discount_rate__gte=30,
        in_stock=True
    ).select_related('brand', 'category').order_by('-discount_rate')[:20]
    
    # 홈페이지 SEO 메타 생성
    seo_generator = SEOMetaGenerator(request)
    meta = seo_generator.generate_home_meta()
    
    # Organization schema
    schema_generator = StructuredDataGenerator(request)
    schemas = [
        schema_generator.generate_organization_schema()
    ]
    
    context = {
        'all_brands': all_brands,
        'categories': categories,
        'new_arrivals': new_arrivals,
        'popular_products': popular_products,
        'mega_deals': mega_deals,
        'meta': meta,
        'schemas': [json.dumps(s, ensure_ascii=False, indent=2) for s in schemas],
    }
    
    return render(request, 'frontend/home.html', context)


def product_detail(request, product_id):
    """상품 상세 페이지 (AI 기능 포함)"""
    from django.http import Http404
    
    try:
        product = GenericProduct.objects.select_related('brand', 'category').get(id=product_id)
    except GenericProduct.DoesNotExist:
        raise Http404("상품을 찾을 수 없습니다")
    
    # SEO 메타
    seo_gen = SEOMetaGenerator(request)
    meta = seo_gen.generate_product_detail_meta(
        product=product,
        brand_name=product.brand.name,
        category_name=product.category.name
    )
    
    # Structured Data
    sd_gen = StructuredDataGenerator(request)
    schema = sd_gen.generate_product_schema(
        product=product,
        brand=product.brand,
        category=product.category
    )
    
    # AI 기능 사용 가능 여부 (임베딩 존재 확인)
    from apps.recommendations.models import ImageEmbedding
    has_embedding = ImageEmbedding.objects.filter(
        product_id=product_id,
        model_version='resnet50'
    ).exists()
    
    context = {
        'product': product,
        'meta': meta,
        'schema': json.dumps(schema, ensure_ascii=False, indent=2),
        'has_embedding': has_embedding,
        'has_material': bool(product.material_composition),
    }
    
    return render(request, 'frontend/product_detail.html', context)


def brand_products(request, brand_slug):
    """특정 브랜드의 모든 상품"""
    brand = get_object_or_404(Brand, slug=brand_slug)
    
    # GenericProduct로 통합 조회
    queryset = GenericProduct.objects.filter(
        brand=brand,
        in_stock=True
    ).select_related('brand', 'category')
    
    # 검색 필터
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(Q(title__icontains=search_query))
    
    # 정렬
    sort = request.GET.get('sort', 'discount')
    if sort == 'discount':
        queryset = queryset.order_by('-discount_rate')
    elif sort == 'price-low':
        queryset = queryset.order_by('price')
    elif sort == 'price-high':
        queryset = queryset.order_by('-price')
    elif sort == 'newest':
        queryset = queryset.order_by('-created_at')
    
    # 페이지네이션
    page_size = int(request.GET.get('page_size', 20))
    page_number = int(request.GET.get('page', 1))
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)
    products = page_obj.object_list
    
    # 페이지 범위 계산
    total_pages = paginator.num_pages
    if total_pages <= 10:
        page_range = range(1, total_pages + 1)
    else:
        if page_number <= 5:
            page_range = list(range(1, 8)) + ['...', total_pages]
        elif page_number >= total_pages - 4:
            page_range = [1, '...'] + list(range(total_pages - 6, total_pages + 1))
        else:
            page_range = [1, '...'] + list(range(page_number - 2, page_number + 3)) + ['...', total_pages]
    
    # 사이드바 데이터 (상품이 있는 브랜드/카테고리만)
    all_brands = Brand.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('brand_id', flat=True).distinct()
    ).order_by('name')
    categories = Category.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('category_id', flat=True).distinct()
    )
    
    context = {
        'brand': brand,
        'category': None,
        'products': products,
        'total': paginator.count,
        'page': page_number,
        'page_size': page_size,
        'total_pages': total_pages,
        'page_range': page_range,
        'sort': sort,
        'search_query': search_query,
        'view_type': 'brand',
        'all_brands': all_brands,
        'categories': categories,
    }
    
    return render(request, 'frontend/landing.html', context)


def category_products(request, category_slug):
    """특정 카테고리의 모든 상품 (모든 브랜드)"""
    category = get_object_or_404(Category, slug=category_slug)
    
    # GenericProduct로 통합 조회
    queryset = GenericProduct.objects.filter(
        category=category,
        in_stock=True
    ).select_related('brand', 'category')
    
    # 카테고리에 속한 브랜드 목록 (상품이 있는 브랜드만, 필터 전 기준)
    available_brands = Brand.objects.filter(
        id__in=queryset.values_list('brand_id', flat=True).distinct()
    ).order_by('name')
    
    # 필터
    filters = {}
    
    # 브랜드 필터 (다중 선택 가능)
    brand_slugs = request.GET.getlist('brands')
    if brand_slugs:
        queryset = queryset.filter(brand__slug__in=brand_slugs)
        filters['brands'] = brand_slugs
    
    # 가격 필터
    price_min = request.GET.get('priceMin')
    price_max = request.GET.get('priceMax')
    if price_min:
        queryset = queryset.filter(price__gte=int(price_min))
        filters['priceMin'] = price_min
    if price_max:
        queryset = queryset.filter(price__lte=int(price_max))
        filters['priceMax'] = price_max
    
    # 할인율 필터
    discount_min = request.GET.get('discountMin')
    if discount_min:
        queryset = queryset.filter(discount_rate__gte=int(discount_min))
        filters['discountMin'] = discount_min
    
    # 검색 필터
    search_query = request.GET.get('search', '').strip()
    if search_query:
        queryset = queryset.filter(Q(title__icontains=search_query))
    
    # 정렬
    sort = request.GET.get('sort', 'discount')
    if sort == 'discount':
        queryset = queryset.order_by('-discount_rate')
    elif sort == 'price-low':
        queryset = queryset.order_by('price')
    elif sort == 'price-high':
        queryset = queryset.order_by('-price')
    elif sort == 'newest':
        queryset = queryset.order_by('-created_at')
    
    # 페이지네이션
    page_size = int(request.GET.get('page_size', 20))
    page_number = int(request.GET.get('page', 1))
    
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page_number)
    products = page_obj.object_list
    
    # 페이지 범위 계산
    total_pages = paginator.num_pages
    if total_pages <= 10:
        page_range = range(1, total_pages + 1)
    else:
        if page_number <= 5:
            page_range = list(range(1, 8)) + ['...', total_pages]
        elif page_number >= total_pages - 4:
            page_range = [1, '...'] + list(range(total_pages - 6, total_pages + 1))
        else:
            page_range = [1, '...'] + list(range(page_number - 2, page_number + 3)) + ['...', total_pages]
    
    # 사이드바 데이터 (상품이 있는 브랜드/카테고리만)
    all_brands = Brand.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('brand_id', flat=True).distinct()
    ).order_by('name')
    categories = Category.objects.filter(
        id__in=GenericProduct.objects.filter(in_stock=True).values_list('category_id', flat=True).distinct()
    )
    
    context = {
        'brand': None,
        'category': category,
        'products': products,
        'total': paginator.count,
        'page': page_number,
        'page_size': page_size,
        'total_pages': total_pages,
        'page_range': page_range,
        'sort': sort,
        'search_query': search_query,
        'filters': filters,
        'view_type': 'category',
        'all_brands': all_brands,
        'categories': categories,
        'available_brands': available_brands,
    }
    
    return render(request, 'frontend/landing.html', context)


