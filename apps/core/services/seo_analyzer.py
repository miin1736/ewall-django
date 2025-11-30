"""
SEO 분석 및 모니터링 서비스
"""
from typing import Dict, List, Any, Optional
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class SEOAnalyzer:
    """SEO 성능 분석 서비스
    
    Features:
        - 메타 태그 검증
        - Schema.org 검증
        - 이미지 최적화 체크
        - 페이지 속도 분석
        - 색인 상태 모니터링
    """
    
    def __init__(self):
        self.recommendations = []
    
    def analyze_meta_tags(self, meta: Dict[str, Any]) -> Dict[str, Any]:
        """메타 태그 분석
        
        Args:
            meta: SEOMetaGenerator가 생성한 메타 데이터
        
        Returns:
            분석 결과 및 권장사항
        """
        issues = []
        score = 100
        
        # Title 검증
        if 'title' in meta:
            title_len = len(meta['title'])
            if title_len < 30:
                issues.append({
                    'severity': 'warning',
                    'field': 'title',
                    'message': f'제목이 너무 짧습니다 ({title_len}자). 30-60자 권장'
                })
                score -= 10
            elif title_len > 60:
                issues.append({
                    'severity': 'warning',
                    'field': 'title',
                    'message': f'제목이 너무 깁니다 ({title_len}자). 30-60자 권장'
                })
                score -= 5
        else:
            issues.append({
                'severity': 'error',
                'field': 'title',
                'message': '제목이 없습니다'
            })
            score -= 20
        
        # Description 검증
        if 'description' in meta:
            desc_len = len(meta['description'])
            if desc_len < 50:
                issues.append({
                    'severity': 'warning',
                    'field': 'description',
                    'message': f'설명이 너무 짧습니다 ({desc_len}자). 120-160자 권장'
                })
                score -= 10
            elif desc_len > 160:
                issues.append({
                    'severity': 'error',
                    'field': 'description',
                    'message': f'설명이 너무 깁니다 ({desc_len}자). 160자 제한'
                })
                score -= 15
        else:
            issues.append({
                'severity': 'error',
                'field': 'description',
                'message': '설명이 없습니다'
            })
            score -= 20
        
        # OG 태그 검증
        if 'og' not in meta:
            issues.append({
                'severity': 'warning',
                'field': 'og',
                'message': 'Open Graph 태그가 없습니다'
            })
            score -= 10
        else:
            required_og = ['title', 'description', 'url', 'image']
            for field in required_og:
                if field not in meta['og']:
                    issues.append({
                        'severity': 'warning',
                        'field': f'og:{field}',
                        'message': f'OG {field}가 없습니다'
                    })
                    score -= 5
        
        # Canonical URL 검증
        if 'canonical_url' not in meta:
            issues.append({
                'severity': 'warning',
                'field': 'canonical_url',
                'message': 'Canonical URL이 없습니다'
            })
            score -= 5
        
        return {
            'score': max(0, score),
            'issues': issues,
            'recommendations': self._generate_meta_recommendations(issues)
        }
    
    def analyze_schema(self, schemas: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Schema.org 구조화 데이터 분석
        
        Args:
            schemas: JSON-LD 스키마 리스트
        
        Returns:
            분석 결과
        """
        issues = []
        score = 100
        
        if not schemas:
            return {
                'score': 0,
                'issues': [{
                    'severity': 'error',
                    'message': '구조화 데이터가 없습니다'
                }],
                'recommendations': ['Product, Organization, Breadcrumb 스키마를 추가하세요']
            }
        
        # 스키마 타입 확인
        schema_types = [s.get('@type') for s in schemas if '@type' in s]
        
        recommended_types = ['Product', 'Organization', 'BreadcrumbList']
        for schema_type in recommended_types:
            if schema_type not in schema_types:
                issues.append({
                    'severity': 'warning',
                    'field': 'schema',
                    'message': f'{schema_type} 스키마가 없습니다'
                })
                score -= 10
        
        # Product 스키마 상세 검증
        product_schemas = [s for s in schemas if s.get('@type') == 'Product']
        for product_schema in product_schemas:
            if 'offers' not in product_schema:
                issues.append({
                    'severity': 'warning',
                    'field': 'Product.offers',
                    'message': 'Product에 offers가 없습니다'
                })
                score -= 10
            
            if 'brand' not in product_schema:
                issues.append({
                    'severity': 'info',
                    'field': 'Product.brand',
                    'message': 'Product에 brand가 없습니다 (선택사항)'
                })
        
        return {
            'score': max(0, score),
            'schema_types': schema_types,
            'issues': issues,
            'recommendations': self._generate_schema_recommendations(schema_types)
        }
    
    def analyze_images(self, products: List[Any]) -> Dict[str, Any]:
        """이미지 최적화 분석
        
        Args:
            products: 상품 리스트
        
        Returns:
            이미지 분석 결과
        """
        total = len(products)
        missing_images = 0
        missing_alt = 0
        not_webp = 0
        
        for product in products:
            if not hasattr(product, 'image_url') or not product.image_url:
                missing_images += 1
            else:
                if not product.image_url.endswith('.webp'):
                    not_webp += 1
            
            if not hasattr(product, 'title') or not product.title:
                missing_alt += 1
        
        score = 100
        issues = []
        
        if missing_images > 0:
            ratio = (missing_images / total) * 100
            issues.append({
                'severity': 'error',
                'message': f'{missing_images}개 상품에 이미지가 없습니다 ({ratio:.1f}%)'
            })
            score -= ratio
        
        if not_webp > total * 0.5:
            issues.append({
                'severity': 'warning',
                'message': f'{not_webp}개 이미지가 WebP가 아닙니다. WebP 변환 권장'
            })
            score -= 20
        
        return {
            'score': max(0, score),
            'total_products': total,
            'missing_images': missing_images,
            'not_webp': not_webp,
            'webp_ratio': ((total - not_webp) / total * 100) if total > 0 else 0,
            'issues': issues,
            'recommendations': self._generate_image_recommendations(not_webp, total)
        }
    
    def get_overall_score(
        self,
        meta_score: int,
        schema_score: int,
        image_score: int
    ) -> Dict[str, Any]:
        """종합 SEO 점수 계산
        
        Args:
            meta_score: 메타 태그 점수
            schema_score: 스키마 점수
            image_score: 이미지 점수
        
        Returns:
            종합 점수 및 등급
        """
        # 가중 평균 (메타 40%, 스키마 35%, 이미지 25%)
        overall = (meta_score * 0.4) + (schema_score * 0.35) + (image_score * 0.25)
        
        # 등급 결정
        if overall >= 90:
            grade = 'A'
        elif overall >= 80:
            grade = 'B'
        elif overall >= 70:
            grade = 'C'
        elif overall >= 60:
            grade = 'D'
        else:
            grade = 'F'
        
        return {
            'overall_score': round(overall, 1),
            'grade': grade,
            'meta_score': meta_score,
            'schema_score': schema_score,
            'image_score': image_score,
            'analysis_date': timezone.now().isoformat()
        }
    
    def _generate_meta_recommendations(self, issues: List[Dict]) -> List[str]:
        """메타 태그 권장사항 생성"""
        recommendations = []
        
        for issue in issues:
            if issue['field'] == 'title':
                recommendations.append('제목을 30-60자로 작성하고 주요 키워드를 포함하세요')
            elif issue['field'] == 'description':
                recommendations.append('설명을 120-160자로 작성하고 행동 유도 문구를 포함하세요')
            elif 'og' in issue['field']:
                recommendations.append('Open Graph 태그를 모두 추가하여 소셜 공유를 최적화하세요')
        
        return list(set(recommendations))
    
    def _generate_schema_recommendations(self, existing_types: List[str]) -> List[str]:
        """스키마 권장사항 생성"""
        recommendations = []
        
        if 'Product' not in existing_types:
            recommendations.append('Product 스키마를 추가하여 상품 정보를 구조화하세요')
        if 'Organization' not in existing_types:
            recommendations.append('Organization 스키마를 추가하여 브랜드 신뢰도를 높이세요')
        if 'BreadcrumbList' not in existing_types:
            recommendations.append('BreadcrumbList 스키마로 네비게이션을 개선하세요')
        
        if not recommendations:
            recommendations.append('모든 필수 스키마가 구현되었습니다')
        
        return recommendations
    
    def _generate_image_recommendations(self, not_webp: int, total: int) -> List[str]:
        """이미지 권장사항 생성"""
        recommendations = []
        
        if not_webp > 0:
            recommendations.append(f'{not_webp}개 이미지를 WebP로 변환하여 로딩 속도를 개선하세요')
        
        recommendations.append('모든 이미지에 의미 있는 alt 텍스트를 추가하세요')
        recommendations.append('Lazy loading을 구현하여 초기 로딩 속도를 개선하세요')
        
        return recommendations


class SEOMonitor:
    """SEO 성능 모니터링 서비스
    
    Features:
        - 색인 상태 추적
        - 검색 노출 모니터링
        - 성능 지표 추적
    """
    
    def __init__(self):
        self.metrics = {}
    
    def track_page_view(self, url: str, referrer: Optional[str] = None):
        """페이지 조회 추적
        
        Args:
            url: 페이지 URL
            referrer: 리퍼러 URL
        """
        # Analytics 모델에 저장 (구현 필요)
        logger.info(f"Page view: {url} (referrer: {referrer})")
    
    def get_seo_metrics(self, days: int = 30) -> Dict[str, Any]:
        """SEO 지표 조회
        
        Args:
            days: 조회 기간 (일)
        
        Returns:
            SEO 성능 지표
        """
        from apps.products.models import Product
        from apps.analytics.models import Click
        
        start_date = timezone.now() - timedelta(days=days)
        
        # 상품 통계
        total_products = Product.objects.filter(is_active=True).count()
        
        # 클릭 통계
        total_clicks = Click.objects.filter(created_at__gte=start_date).count()
        
        # 상위 검색어 (구현 필요)
        top_keywords = []
        
        return {
            'period_days': days,
            'total_products': total_products,
            'total_clicks': total_clicks,
            'avg_clicks_per_day': round(total_clicks / days, 1) if days > 0 else 0,
            'top_keywords': top_keywords,
            'last_updated': timezone.now().isoformat()
        }
