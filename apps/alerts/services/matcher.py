"""
Alert matching service
알림 조건 매칭 로직
"""
from typing import Dict, Any
from django.db.models import Model


class AlertMatcher:
    """알림 조건 매칭"""
    
    @staticmethod
    def matches(product: Model, conditions: Dict[str, Any]) -> bool:
        """상품이 알림 조건과 일치하는지 확인
        
        Args:
            product: 상품 모델 인스턴스
            conditions: 알림 조건 딕셔너리
        
        Returns:
            매칭 여부
        """
        # 가격 조건
        if 'priceBelow' in conditions:
            if float(product.price) > conditions['priceBelow']:
                return False
        
        # 할인율 조건
        if 'discountAtLeast' in conditions:
            if float(product.discount_rate) < conditions['discountAtLeast']:
                return False
        
        # 카테고리별 속성 조건
        category_slug = product.category.slug
        
        if category_slug == 'down':
            # 다운 비율
            if 'downRatio' in conditions:
                if not hasattr(product, 'down_ratio') or product.down_ratio != conditions['downRatio']:
                    return False
            
            # 필파워 최소값
            if 'fillPowerMin' in conditions:
                if not hasattr(product, 'fill_power') or not product.fill_power:
                    return False
                if product.fill_power < conditions['fillPowerMin']:
                    return False
            
            # 후드
            if 'hood' in conditions:
                if not hasattr(product, 'hood') or product.hood != conditions['hood']:
                    return False
        
        elif category_slug == 'slacks':
            # 허리 타입
            if 'waistType' in conditions:
                if not hasattr(product, 'waist_type') or product.waist_type != conditions['waistType']:
                    return False
            
            # 밑단 형태
            if 'legOpening' in conditions:
                if not hasattr(product, 'leg_opening') or product.leg_opening != conditions['legOpening']:
                    return False
        
        elif category_slug == 'jeans':
            # 워싱
            if 'wash' in conditions:
                if not hasattr(product, 'wash') or product.wash != conditions['wash']:
                    return False
            
            # 컷
            if 'cut' in conditions:
                if not hasattr(product, 'cut') or product.cut != conditions['cut']:
                    return False
        
        # 공통 속성
        if 'fit' in conditions:
            if not hasattr(product, 'fit') or product.fit != conditions['fit']:
                return False
        
        if 'shell' in conditions:
            if not hasattr(product, 'shell') or product.shell != conditions['shell']:
                return False
        
        # 모든 조건 통과
        return True
