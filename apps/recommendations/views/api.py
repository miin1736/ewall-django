"""
Recommendation REST API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class ProductRecommendationsAPIView(APIView):
    """상품 기반 추천 API
    
    GET /api/recommendations/products/<product_id>/
        - 특정 상품과 유사한 상품 추천
        - 협업 필터링 + 인기 기반 하이브리드
    
    Query Parameters:
        - limit: 반환할 추천 수 (기본 10)
        - category: 카테고리 필터
        - brand: 브랜드 필터
        - algorithm: cf (협업 필터링), popular (인기 기반), hybrid (하이브리드, 기본값)
    """
    
    def get(self, request, product_id: str):
        """상품 추천 조회"""
        limit = int(request.query_params.get('limit', 10))
        category = request.query_params.get('category')
        brand = request.query_params.get('brand')
        algorithm = request.query_params.get('algorithm', 'hybrid')
        
        try:
            if algorithm == 'cf':
                from apps.recommendations.services.collaborative_filter import CollaborativeFilter
                recommender = CollaborativeFilter()
                recommendations = recommender.get_recommendations(
                    product_id=product_id,
                    limit=limit,
                    category=category,
                    brand=brand
                )
            elif algorithm == 'popular':
                from apps.recommendations.services.popularity_recommender import PopularityRecommender
                recommender = PopularityRecommender()
                recommendations = recommender.get_popular_products(
                    category=category,
                    brand=brand,
                    limit=limit,
                    exclude_ids=[product_id]
                )
            else:  # hybrid
                from apps.recommendations.services.hybrid_recommender import HybridRecommender
                recommender = HybridRecommender()
                recommendations = recommender.get_recommendations(
                    product_id=product_id,
                    limit=limit,
                    category=category,
                    brand=brand
                )
            
            # 응답 데이터 구성
            results = []
            for rec in recommendations:
                product = rec['product']
                results.append({
                    'id': product.id,
                    'title': product.title,
                    'brand': product.brand.name,
                    'category': product.category.name,
                    'price': str(product.price),
                    'original_price': str(product.original_price),
                    'discount_rate': str(product.discount_rate),
                    'image_url': product.image_url,
                    'url': product.deeplink,
                    'score': rec['score'],
                    'reason': rec['reason']
                })
            
            return Response({
                'product_id': product_id,
                'algorithm': algorithm,
                'count': len(results),
                'recommendations': results
            })
            
        except Exception as e:
            logger.error(f"Recommendation error for product {product_id}: {str(e)}")
            return Response(
                {'error': 'Failed to generate recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class PersonalizedRecommendationsAPIView(APIView):
    """개인화 추천 API
    
    GET /api/recommendations/personalized/
        - 사용자 세션 기반 개인화 추천
        - 최근 상호작용 기록 분석
    
    Query Parameters:
        - limit: 반환할 추천 수 (기본 10)
        - category: 카테고리 필터
    """
    
    def get(self, request):
        """개인화 추천 조회"""
        session_id = request.session.session_key
        
        if not session_id:
            # 세션이 없으면 생성
            request.session.create()
            session_id = request.session.session_key
        
        limit = int(request.query_params.get('limit', 10))
        category = request.query_params.get('category')
        
        try:
            from apps.recommendations.services.hybrid_recommender import HybridRecommender
            
            recommender = HybridRecommender()
            recommendations = recommender.get_personalized_recommendations(
                session_id=session_id,
                limit=limit,
                category=category
            )
            
            # 응답 데이터 구성
            results = []
            for rec in recommendations:
                product = rec['product']
                results.append({
                    'id': product.id,
                    'title': product.title,
                    'brand': product.brand.name,
                    'category': product.category.name,
                    'price': str(product.price),
                    'original_price': str(product.original_price),
                    'discount_rate': str(product.discount_rate),
                    'image_url': product.image_url,
                    'url': product.deeplink,
                    'score': rec['score'],
                    'reason': rec['reason']
                })
            
            return Response({
                'session_id': session_id,
                'count': len(results),
                'recommendations': results
            })
            
        except Exception as e:
            logger.error(f"Personalized recommendation error: {str(e)}")
            return Response(
                {'error': 'Failed to generate personalized recommendations'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrendingProductsAPIView(APIView):
    """트렌딩 상품 API
    
    GET /api/recommendations/trending/
        - 최근 급상승 인기 상품
    
    Query Parameters:
        - limit: 반환할 상품 수 (기본 10)
        - category: 카테고리 필터
        - hours: 분석할 최근 N시간 (기본 24)
    """
    
    def get(self, request):
        """트렌딩 상품 조회"""
        limit = int(request.query_params.get('limit', 10))
        category = request.query_params.get('category')
        hours = int(request.query_params.get('hours', 24))
        
        try:
            from apps.recommendations.services.popularity_recommender import PopularityRecommender
            
            recommender = PopularityRecommender()
            trending = recommender.get_trending_products(
                category=category,
                limit=limit,
                hours=hours
            )
            
            # 응답 데이터 구성
            results = []
            for item in trending:
                product = item['product']
                results.append({
                    'id': product.id,
                    'title': product.title,
                    'brand': product.brand.name,
                    'category': product.category.name,
                    'price': str(product.price),
                    'original_price': str(product.original_price),
                    'discount_rate': str(product.discount_rate),
                    'image_url': product.image_url,
                    'url': product.deeplink,
                    'interaction_count': item['score'],
                    'reason': item['reason']
                })
            
            return Response({
                'hours_analyzed': hours,
                'count': len(results),
                'trending': results
            })
            
        except Exception as e:
            logger.error(f"Trending products error: {str(e)}")
            return Response(
                {'error': 'Failed to get trending products'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class TrackInteractionAPIView(APIView):
    """상호작용 추적 API
    
    POST /api/recommendations/track/
        - 사용자 상호작용 기록
    
    Body:
        - product_id: 상품 ID
        - interaction_type: view, click, alert
    """
    
    def post(self, request):
        """상호작용 기록"""
        session_id = request.session.session_key
        
        if not session_id:
            request.session.create()
            session_id = request.session.session_key
        
        product_id = request.data.get('product_id')
        interaction_type = request.data.get('interaction_type', 'view')
        
        if not product_id:
            return Response(
                {'error': 'product_id is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # 상품 정보 조회
            from apps.products.models import (
                DownProduct, SlacksProduct, JeansProduct,
                CrewneckProduct, LongSleeveProduct, CoatProduct
            )
            
            product = None
            models = [DownProduct, SlacksProduct, JeansProduct,
                      CrewneckProduct, LongSleeveProduct, CoatProduct]
            
            for model in models:
                try:
                    product = model.objects.get(id=product_id)
                    break
                except model.DoesNotExist:
                    continue
            
            if not product:
                return Response(
                    {'error': 'Product not found'},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # 가중치 설정
            weight_map = {
                'view': 0.5,
                'click': 1.0,
                'alert': 1.5,
                'purchase': 3.0
            }
            weight = weight_map.get(interaction_type, 0.5)
            
            # 상호작용 기록
            from apps.recommendations.models import UserProductInteraction
            
            interaction = UserProductInteraction.objects.create(
                session_id=session_id,
                user_email=request.user.email if request.user.is_authenticated else None,
                product_id=product_id,
                product_category=product.category.slug,
                product_brand=product.brand.slug,
                interaction_type=interaction_type,
                weight=weight
            )
            
            return Response({
                'success': True,
                'interaction_id': interaction.id,
                'session_id': session_id,
                'product_id': product_id,
                'interaction_type': interaction_type,
                'weight': weight
            })
            
        except Exception as e:
            logger.error(f"Track interaction error: {str(e)}")
            return Response(
                {'error': 'Failed to track interaction'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
