"""
Image similarity recommendation API views - Version 2
개선된 AI 기능:
1. 질감 생성: 실제 소재 구성(material_composition) 기반 상세 질감 표현
2. 유사도 검색: 같은 카테고리 내 비슷한 스타일 의류 추천
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.core.cache import cache
import logging

from apps.products.models import GenericProduct
from apps.recommendations.models import ImageEmbedding
from apps.recommendations.services.image_embedding import ImageEmbeddingService
from apps.recommendations.services.faiss_manager import FaissIndexManager
from apps.recommendations.services.texture_generator import TextureGeneratorService

logger = logging.getLogger(__name__)


def get_product_by_id(product_id):
    """Get product from any model by product_id."""
    try:
        return GenericProduct.objects.get(id=product_id)
    except GenericProduct.DoesNotExist:
        return None


class SimilarImagesV2APIView(APIView):
    """
    같은 카테고리 내에서 비슷한 스타일의 의류를 추천하는 API
    
    GET /api/recommendations/v2/similar-images/<product_id>/
    Query params:
    - limit: 추천 개수 (default: 10, max: 50)
    - min_similarity: 최소 유사도 (0-1, default: 0.5)
    """
    
    def get(self, request, product_id):
        """같은 카테고리 내 비슷한 스타일 상품 추천"""
        # AI 패키지 가용성 체크
        from apps.recommendations.services.image_embedding import AI_AVAILABLE, MISSING_PACKAGES as IMG_MISSING
        from apps.recommendations.services.faiss_manager import FAISS_AVAILABLE, MISSING_PACKAGES as FAISS_MISSING
        
        if not AI_AVAILABLE or not FAISS_AVAILABLE:
            missing_all = list(set(IMG_MISSING + FAISS_MISSING))
            return Response({
                'error': 'AI 기능을 사용할 수 없습니다',
                'missing_packages': missing_all,
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        
        try:
            # 파라미터 파싱
            limit = min(int(request.query_params.get('limit', 10)), 50)
            min_similarity = float(request.query_params.get('min_similarity', 0.5))
            
            # 원본 상품 조회
            source_product = get_product_by_id(product_id)
            if not source_product:
                return Response(
                    {'error': f'상품 {product_id}를 찾을 수 없습니다'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            source_category = source_product.category.slug if hasattr(source_product, 'category') else None
            
            # 임베딩 생성 또는 조회
            embedding_vector = self._get_or_create_embedding(source_product)
            if embedding_vector is None:
                return Response({
                    'error': '이미지 분석에 실패했습니다',
                    'source_product': {
                        'id': product_id,
                        'name': source_product.title
                    }
                }, status=status.HTTP_200_OK)
            
            # Faiss로 유사 상품 검색
            faiss_manager = FaissIndexManager()
            if faiss_manager.index.ntotal == 0:
                return Response({
                    'error': '인덱스가 비어있습니다',
                    'message': 'generate_embeddings 명령을 먼저 실행해주세요'
                })
            
            # 검색 (여유분 포함)
            search_results = faiss_manager.search(
                query_vector=embedding_vector,
                k=limit * 3,
                exclude_product_id=product_id
            )
            
            # 필터링: 같은 카테고리 + 유사도 기준
            filtered_results = []
            for result in search_results:
                if result['similarity'] < min_similarity:
                    continue
                
                product = get_product_by_id(result['product_id'])
                if not product or not product.in_stock:
                    continue
                
                # 같은 카테고리만
                if source_category and hasattr(product, 'category'):
                    if product.category.slug != source_category:
                        continue
                
                # 스타일 유사도 설명
                style_desc = self._get_style_description(result['similarity'])
                
                filtered_results.append({
                    'product_id': product.id,
                    'name': product.title,
                    'brand': product.brand.name if product.brand else None,
                    'category': product.category.name,
                    'image_url': product.image_url,
                    'price': float(product.price),
                    'discount_rate': float(product.discount_rate),
                    'final_price': float(product.price * (1 - product.discount_rate / 100)),
                    'similarity_score': round(result['similarity'], 4),
                    'style_match': style_desc
                })
                
                if len(filtered_results) >= limit:
                    break
            
            return Response({
                'product_id': product_id,
                'source_product': {
                    'name': source_product.title,
                    'category': source_product.category.name,
                    'image_url': source_product.image_url,
                },
                'similar_products': filtered_results,
                'total_count': len(filtered_results),
                'description': f'"{source_product.category.name}" 카테고리에서 비슷한 스타일의 상품을 추천합니다'
            })
            
        except Exception as e:
            logger.error(f'Error in SimilarImagesV2APIView: {str(e)}', exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _get_style_description(self, similarity: float) -> str:
        """유사도 점수에 따른 스타일 설명"""
        if similarity >= 0.95:
            return '거의 동일한 스타일'
        elif similarity >= 0.85:
            return '매우 비슷한 디자인'
        elif similarity >= 0.75:
            return '비슷한 스타일'
        elif similarity >= 0.65:
            return '유사한 분위기'
        else:
            return '비슷한 카테고리'
    
    def _get_or_create_embedding(self, product):
        """임베딩 조회 또는 생성"""
        try:
            db_embedding = ImageEmbedding.objects.get(
                product_id=product.id,
                model_version='resnet50'
            )
            import numpy as np
            return np.array(db_embedding.embedding_vector, dtype=np.float32)
        except ImageEmbedding.DoesNotExist:
            pass
        
        # 새로 생성
        try:
            embedding_service = ImageEmbeddingService()
            embedding_vector = embedding_service.get_embedding_from_url(
                product.image_url,
                use_cache=False
            )
            
            if embedding_vector is not None:
                ImageEmbedding.objects.update_or_create(
                    product_id=product.id,
                    defaults={
                        'image_url': product.image_url,
                        'embedding_vector': embedding_vector.tolist(),
                        'model_version': 'resnet50'
                    }
                )
            
            return embedding_vector
        except Exception as e:
            logger.error(f'Embedding generation failed: {str(e)}')
            return None


class GenerateTextureV2APIView(APIView):
    """
    실제 소재 구성을 기반으로 질감을 확대하여 상세하게 표현하는 API
    
    POST /api/recommendations/v2/generate-texture/
    Body:
    {
        "product_id": "DOWN001",
        "quality": "high"  // optional: 'high', 'medium', 'low'
    }
    """
    
    def post(self, request):
        """실제 소재 구성 기반 상세 질감 이미지 생성"""
        try:
            product_id = request.data.get('product_id')
            quality = request.data.get('quality', 'high')
            
            if not product_id:
                return Response(
                    {'error': 'product_id is required'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 상품 조회
            product = get_product_by_id(product_id)
            if not product:
                return Response(
                    {'error': f'상품 {product_id}를 찾을 수 없습니다'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 실제 소재 구성 가져오기
            material_composition = getattr(product, 'material_composition', None)
            if not material_composition:
                material_composition = self._infer_material_composition(product)
            
            # 색상 추론
            color = self._infer_color(product)
            
            # 이미지 URL
            image_url = getattr(product, 'image_url', None)
            
            # 질감 생성 서비스
            try:
                generator = TextureGeneratorService()
            except ValueError as e:
                return Response({
                    'error': 'AI 질감 생성 기능을 사용할 수 없습니다',
                    'reason': 'Hugging Face API 토큰이 설정되지 않았습니다',
                    'solution': '환경변수 HUGGING_FACE_API_TOKEN을 설정해주세요'
                }, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            
            logger.info(f"Generating detailed texture: {product_id} - {material_composition}")
            
            # 질감 이미지 생성
            try:
                texture_image = generator.generate_texture(
                    material=material_composition,
                    color=color,
                    product_type=product.category.name if hasattr(product, 'category') else None,
                    quality=quality,
                    reference_image_url=image_url
                )
            except Exception as e:
                logger.error(f'Texture generation failed: {str(e)}')
                return Response(
                    {'error': f'질감 생성 실패: {str(e)}'},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            if not texture_image:
                return Response(
                    {'error': '질감 이미지 생성 실패'},
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
                'model': 'FLUX.1-dev (Hugging Face)',
                'image_size': f'{texture_image.size[0]}x{texture_image.size[1]}',
                'features': [
                    '실제 소재 구성 기반 (' + material_composition + ')',
                    '극도로 확대된 질감',
                    '개별 섬유 패턴 가시화',
                    '전문가급 매크로 포토그래피'
                ]
            })
            
        except Exception as e:
            logger.error(f'Error in GenerateTextureV2APIView: {str(e)}', exc_info=True)
            return Response(
                {'error': str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _infer_material_composition(self, product) -> str:
        """카테고리와 제목에서 소재 구성 추론"""
        title = product.title.lower()
        category = product.category.slug if hasattr(product, 'category') else ''
        
        # 제목 키워드 우선
        if 'wool' in title or '울' in title:
            return 'wool 80%, polyester 20%'
        elif 'cashmere' in title or '캐시미어' in title:
            return 'cashmere 70%, wool 30%'
        elif 'leather' in title or '가죽' in title:
            return 'genuine leather 100%'
        elif 'denim' in title or '데님' in title:
            return 'cotton 98%, elastane 2%'
        
        # 카테고리별 기본값
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
        
        return category_defaults.get(category, 'cotton 95%, polyester 5%')
    
    def _infer_color(self, product) -> str:
        """제목에서 색상 추론"""
        title = product.title.lower()
        
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
        
        return 'natural'
