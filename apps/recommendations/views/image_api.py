"""
Image similarity recommendation API views.
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
from django.conf import settings
from django.db.models import Q
import logging

from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct
)
from apps.recommendations.models import ImageEmbedding
from apps.recommendations.services.image_embedding import ImageEmbeddingService
from apps.recommendations.services.faiss_manager import FaissIndexManager
from apps.recommendations.services.texture_generator import TextureGeneratorService

logger = logging.getLogger(__name__)

# All product models
PRODUCT_MODELS = [
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct
]


def get_product_by_id(product_id):
    """Get product from any model by product_id (which is actually the 'id' field)."""
    for model in PRODUCT_MODELS:
        try:
            return model.objects.get(id=product_id)
        except model.DoesNotExist:
            continue
    return None


def count_products_with_images():
    """Count all products with images across all models."""
    try:
        total = 0
        for model in PRODUCT_MODELS:
            try:
                total += model.objects.exclude(
                    Q(image_url='') | Q(image_url__isnull=True)
                ).count()
            except Exception as e:
                logger.warning(f'Error counting products for {model.__name__}: {str(e)}')
                continue
        return total
    except Exception as e:
        logger.error(f'Error in count_products_with_images: {str(e)}')
        return 0


class SimilarImagesAPIView(APIView):
    """
    API endpoint for image-based product recommendations.
    
    Returns products with similar STYLE from the SAME CATEGORY.
    Uses ResNet50 image embeddings + Faiss similarity search.
    
    GET /api/recommendations/similar-images/<product_id>/
    Query params:
    - limit: Number of similar products to return (default: 10, max: 50)
    - min_similarity: Minimum similarity threshold (0-1, default: 0.5)
    - rebuild: Force rebuild embedding (default: false)
    """
    
    def get(self, request, product_id):
        """Get similar products based on image similarity."""
        # AI 패키지 가용성 체크
        from apps.recommendations.services.image_embedding import AI_AVAILABLE, MISSING_PACKAGES as IMG_MISSING
        from apps.recommendations.services.faiss_manager import FAISS_AVAILABLE, MISSING_PACKAGES as FAISS_MISSING
        
        if not AI_AVAILABLE or not FAISS_AVAILABLE:
            missing_all = list(set(IMG_MISSING + FAISS_MISSING))
            return Response({
                'error': 'AI 기능을 사용할 수 없습니다',
                'reason': '필수 Python 패키지가 설치되지 않았습니다',
                'missing_packages': missing_all,
                'install_command': f'pip install {" ".join(missing_all)}',
                'details': {
                    'image_embedding_available': AI_AVAILABLE,
                    'faiss_available': FAISS_AVAILABLE,
                    'missing_for_embedding': IMG_MISSING,
                    'missing_for_faiss': FAISS_MISSING
                }
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # Parse query parameters
            limit = min(int(request.query_params.get('limit', 10)), 50)
            min_similarity = float(request.query_params.get('min_similarity', 0.5))
            rebuild = request.query_params.get('rebuild', 'false').lower() == 'true'
            
            # Validate parameters
            if limit < 1:
                return Response(
                    {'error': 'Limit must be at least 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            if not (0 <= min_similarity <= 1):
                return Response(
                    {'error': 'min_similarity must be between 0 and 1'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get source product
            source_product = get_product_by_id(product_id)
            if source_product is None:
                return Response(
                    {'error': f'Product {product_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get source product category for filtering
            source_category = source_product.category.slug if hasattr(source_product, 'category') else None
            
            # Check if product has image
            if not source_product.image_url:
                return Response(
                    {'error': 'Product has no image'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get or create embedding for source product
            embedding_vector = self._get_or_create_embedding(
                source_product, 
                rebuild=rebuild
            )
            
            if embedding_vector is None:
                logger.warning(f'Failed to generate embedding for {product_id}, returning empty results')
                return Response({
                    'source_product': {
                        'id': product_id,
                        'name': source_product.title,
                        'category': source_product.category.name if hasattr(source_product, 'category') else 'Unknown'
                    },
                    'similar_products': [],
                    'count': 0,
                    'message': 'Failed to generate embedding. Image may be unavailable.'
                }, status=status.HTTP_200_OK)
            
            # Search similar images using Faiss
            faiss_manager = FaissIndexManager()
            
            # Check if index is empty
            if faiss_manager.index.ntotal == 0:
                logger.warning('Faiss index is empty, returning empty results')
                return Response({
                    'product_id': product_id,
                    'similar_products': [],
                    'total_count': 0,
                    'message': 'No indexed products found. Run generate_embeddings command first.'
                })
            
            # Search for similar products (limit + buffer for filtering)
            search_limit = limit * 3  # Get more results to account for filtering
            similar_results = faiss_manager.search(
                query_vector=embedding_vector,
                k=search_limit,
                exclude_product_id=product_id  # Exclude source product
            )
            
            # Filter by similarity threshold and SAME CATEGORY
            filtered_results = []
            for result in similar_results:
                if result['similarity'] < min_similarity:
                    continue
                
                product = get_product_by_id(result['product_id'])
                if product is None:
                    logger.warning(f'Product {result["product_id"]} not found in database')
                    continue
                
                try:
                    # IMPORTANT: Only show products from the SAME CATEGORY
                    if source_category and hasattr(product, 'category'):
                        if product.category.slug != source_category:
                            continue
                    
                    # Only show in-stock products
                    if not product.in_stock:
                        continue
                    
                    # Determine style similarity description
                    similarity_description = self._get_similarity_description(
                        result['similarity'],
                        source_product,
                        product
                    )
                    
                    filtered_results.append({
                        'product_id': product.id,
                        'name': product.title,
                        'brand': product.brand.name if product.brand else None,
                        'category': product.category.name,
                        'category_slug': product.category.slug,
                        'image_url': product.image_url,
                        'price': float(product.price),
                        'discount_rate': product.discount_rate,
                        'final_price': float(product.price * (1 - product.discount_rate / 100)),
                        'similarity_score': round(result['similarity'], 4),
                        'distance': round(result['distance'], 4),
                        'style_match': similarity_description
                    })
                    
                    # Stop when we have enough results
                    if len(filtered_results) >= limit:
                        break
                        
                except Exception as e:
                    logger.warning(f'Error processing product {result["product_id"]}: {str(e)}')
                    continue
            
            return Response({
                'product_id': product_id,
                'source_product': {
                    'name': source_product.title,
                    'image_url': source_product.image_url,
                    'category': source_product.category.name,
                    'brand': source_product.brand.name if source_product.brand else None,
                },
                'similar_products': filtered_results,
                'total_count': len(filtered_results),
                'search_params': {
                    'limit': limit,
                    'min_similarity': min_similarity,
                    'same_category_only': True
                },
                'description': f'"{source_product.category.name}" 카테고리에서 비슷한 스타일의 상품을 추천합니다'
            })
            
        except ValueError as e:
            return Response(
                {'error': f'Invalid parameter: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
        except Exception as e:
            logger.error(f'Error in SimilarImagesAPIView: {str(e)}', exc_info=True)
            return Response(
                {'error': 'Internal server error'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_or_create_embedding(self, product, rebuild=False):
        """
        Get existing embedding or create new one.
        
        Args:
            product: Product instance
            rebuild: Force rebuild embedding
            
        Returns:
            numpy array or None
        """
        # Check cache first (unless rebuild requested)
        cache_key = f'product_embedding:{product.id}'
        if not rebuild:
            cached_embedding = cache.get(cache_key)
            if cached_embedding is not None:
                return cached_embedding
        
        # Check database
        if not rebuild:
            try:
                db_embedding = ImageEmbedding.objects.get(
                    product_id=product.id,
                    model_version='resnet50'
                )
                # Convert JSON list to numpy array
                import numpy as np
                embedding_vector = np.array(db_embedding.embedding_vector, dtype=np.float32)
                
                # Cache for 1 hour
                cache.set(cache_key, embedding_vector, timeout=3600)
                return embedding_vector
                
            except ImageEmbedding.DoesNotExist:
                pass
        
        # Generate new embedding
        try:
            embedding_service = ImageEmbeddingService()
            embedding_vector = embedding_service.get_embedding_from_url(
                product.image_url,
                use_cache=False  # 캐시 비활성화 (Redis 연결 오류 방지)
            )
        except Exception as e:
            logger.error(f'Failed to generate embedding for {product.id}: {str(e)}')
            return None
        
        if embedding_vector is not None:
            # Save to database
            ImageEmbedding.objects.update_or_create(
                product_id=product.id,
                defaults={
                    'image_url': product.image_url,
                    'embedding_vector': embedding_vector.tolist(),  # Convert numpy to list
                    'model_version': 'resnet50'
                }
            )
            
            # Cache for 1 hour
            cache.set(cache_key, embedding_vector, timeout=3600)
        
        return embedding_vector


class ImageIndexStatsAPIView(APIView):
    """
    API endpoint for Faiss index statistics.
    
    GET /api/recommendations/image-index-stats/
    """
    
    def get(self, request):
        """Get statistics about the Faiss index."""
        try:
            try:
                faiss_manager = FaissIndexManager()
                stats = faiss_manager.get_stats()
            except Exception as e:
                logger.error(f'Failed to load Faiss index: {str(e)}')
                stats = {
                    'total_vectors': 0,
                    'dimension': 2048,
                    'index_file_exists': False
                }
            
            # Get database stats
            db_embedding_count = ImageEmbedding.objects.count()
            db_products_with_images = count_products_with_images()
            
            return Response({
                'faiss_index': stats,
                'database': {
                    'total_embeddings': db_embedding_count,
                    'products_with_images': db_products_with_images,
                    'coverage_rate': round(
                        (db_embedding_count / db_products_with_images * 100) 
                        if db_products_with_images > 0 else 0,
                        2
                    )
                },
                'status': 'healthy' if stats['index_file_exists'] else 'index_not_built'
            })
            
        except Exception as e:
            logger.error(f'Error in ImageIndexStatsAPIView: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class GenerateTextureAPIView(APIView):
    """
    AI 질감 상세 이미지 생성 API
    
    실제 상품의 소재 구성(material_composition)과 이미지를 참고하여
    해당 의류의 질감을 확대하여 보다 상세하게 표현합니다.
    
    POST /api/recommendations/generate-texture/
    Body:
    {
        "product_id": "DOWN001",
        "quality": "high"  // optional: 'high', 'medium', 'low'
    }
    
    Response:
    {
        "success": true,
        "product_id": "DOWN001",
        "product_name": "코오롱스포츠 프리미엄 다운 재킷",
        "material_composition": "nylon 85%, polyester 15%",
        "texture_image": "data:image/jpeg;base64,...",
        "description": "실제 소재를 기반으로 한 확대 질감 이미지",
        "model": "FLUX.1-dev"
    }
    """
    
    def post(self, request):
        """질감 이미지 생성 - 실제 소재 구성 반영"""
        try:
            # Request body 파싱
            product_id = request.data.get('product_id')
            quality = request.data.get('quality', 'high')
            
            # Validation
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 상품 조회
            product = get_product_by_id(product_id)
            if not product:
                return Response(
                    {'error': f'Product {product_id} not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 실제 소재 구성 가져오기
            material_composition = getattr(product, 'material_composition', None)
            if not material_composition:
                material_composition = self._infer_material_composition(product)
            
            # 색상 추론
            color = self._infer_color(product)
            
            # 상품 이미지 URL
            image_url = getattr(product, 'image_url', None)
            
            # 질감 생성 서비스 초기화
            try:
                generator = TextureGeneratorService()
            except ValueError as e:
                # API 토큰이 없을 때 발생하는 ValueError 처리
                logger.error(f'TextureGeneratorService initialization failed: {str(e)}')
                return Response({
                    'error': 'AI 질감 생성 기능을 사용할 수 없습니다',
                    'reason': 'Hugging Face API 토큰이 설정되지 않았습니다',
                    'details': {
                        'solution': '환경변수 HUGGING_FACE_API_TOKEN을 설정해주세요'
                    },
                    'instructions': {
                        '1': 'Hugging Face 계정 생성: https://huggingface.co/join',
                        '2': 'API 토큰 발급: https://huggingface.co/settings/tokens',
                        '3': '.env 파일에 HUGGING_FACE_API_TOKEN=your_token_here 추가',
                        '4': '서버 재시작'
                    }
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            except Exception as e:
                logger.error(f'Failed to initialize TextureGeneratorService: {str(e)}')
                return Response(
                    {'error': f'Service initialization failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # 질감 이미지 생성
            logger.info(f"Generating detailed texture for {product_id}: {material_composition}")
            
            try:
                texture_image = generator.generate_texture(
                    material=material_composition,
                    color=color,
                    product_type=product.category.name if hasattr(product, 'category') else None,
                    quality=quality,
                    reference_image_url=image_url
                )
            except Exception as e:
                logger.error(f'Failed to generate texture: {str(e)}')
                return Response(
                    {'error': f'Texture generation failed: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if not texture_image:
                return Response(
                    {'error': 'Failed to generate texture image'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Base64 인코딩
            texture_base64 = generator.image_to_base64(texture_image)
            
            return Response({
                'success': True,
                'product_id': product_id,
                'product_name': product.title,
                'material_composition': material_composition,
                'color': color,
                'quality': quality,
                'texture_image': texture_base64,
                'description': '실제 상품의 소재 구성을 반영하여 확대한 상세 질감 이미지',
                'model': 'FLUX.1-dev (Hugging Face Inference Providers)',
                'image_size': f'{texture_image.size[0]}x{texture_image.size[1]}',
                'features': [
                    '실제 소재 구성 기반',
                    '극도로 확대된 질감',
                    '개별 섬유 패턴 가시화',
                    '전문가급 매크로 포토그래피'
                ]
            })
            
        except Exception as e:
            logger.error(f'Error in GenerateTextureAPIView: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _infer_material_composition(self, product) -> str:
        """상품 카테고리와 제목에서 소재 구성 추론
        
        Args:
            product: Product 객체
        
        Returns:
            소재 구성 문자열 (e.g., "cotton 95%, elastane 5%")
        """
        title = product.title.lower()
        category = product.category.slug if hasattr(product, 'category') else ''
        
        # 카테고리별 일반적인 소재 구성
        category_defaults = {
            'down': 'nylon 85%, polyester 15%',
            'coat': 'wool 70%, polyester 30%',
            'jeans': 'cotton 98%, elastane 2%',
            'slacks': 'polyester 65%, rayon 30%, elastane 5%',
            'crew': 'cotton 95%, elastane 5%',
            'crewneck': 'cotton 95%, elastane 5%',
            'long': 'cotton 95%, elastane 5%',
            'long-sleeve': 'cotton 95%, elastane 5%',
        }
        
        # 제목에서 특수 소재 키워드 감지
        if 'wool' in title or '울' in title:
            return 'wool 80%, polyester 20%'
        elif 'cashmere' in title or '캐시미어' in title:
            return 'cashmere 70%, wool 30%'
        elif 'leather' in title or '가죽' in title:
            return 'genuine leather 100%'
        elif 'denim' in title or '데님' in title:
            return 'cotton 98%, elastane 2%'
        
        return category_defaults.get(category, 'cotton 95%, polyester 5%')
    
    def _infer_color(self, product) -> str:
        """상품명에서 색상 추론"""
        title = product.title.lower()
        
        # 색상 키워드 매칭
        colors = {
            'navy blue': ['네이비', 'navy'],
            'black': ['블랙', 'black', '검정'],
            'white': ['화이트', 'white', '흰색'],
            'beige': ['베이지', 'beige'],
            'gray': ['그레이', 'gray', 'grey', '회색'],
            'blue': ['블루', 'blue', '파랑'],
            'red': ['레드', 'red', '빨강'],
            'green': ['그린', 'green', '초록'],
        }
        
        for color, keywords in colors.items():
            if any(kw in title for kw in keywords):
                return color
        
        return 'natural'  # 기본값


class AvailableProductsAPIView(APIView):
    """이미지 임베딩이 있는 상품 목록 조회"""
    
    def get(self, request):
        """
        GET /api/recommendations/available-products/
        
        Response:
            {
                "count": 10,
                "products": [
                    {
                        "product_id": "DOWN-KOLON-SPORT-001",
                        "name": "다운 재킷",
                        "category": "down",
                        "brand": "Kolon Sport",
                        "has_embedding": true
                    }
                ]
            }
        """
        try:
            # 이미지 임베딩이 있는 상품 ID 가져오기
            embeddings = ImageEmbedding.objects.all().values_list('product_id', flat=True)
            
            products_info = []
            
            for product_id in embeddings:
                # 상품 정보 가져오기
                product = get_product_by_id(product_id)
                if product:
                    products_info.append({
                        'product_id': product.id,
                        'name': product.title,
                        'category': product.category.slug if hasattr(product, 'category') else 'unknown',
                        'brand': product.brand.name if hasattr(product, 'brand') else 'unknown',
                        'has_embedding': True
                    })
            
            # 카테고리별로 정렬
            products_info.sort(key=lambda x: (x['category'], x['product_id']))
            
            return Response({
                'count': len(products_info),
                'products': products_info
            })
            
        except Exception as e:
            logger.error(f'Error in AvailableProductsAPIView: {str(e)}', exc_info=True)
            return Response(
                {'error': f'Internal server error: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

