"""
Alert Condition Builder
복합 조건 빌더 및 유효성 검증
"""
from typing import Dict, Any, List, Optional
from decimal import Decimal
import logging

logger = logging.getLogger(__name__)


class AlertConditionBuilder:
    """알림 조건 빌더
    
    Features:
        - AND/OR 복합 조건 지원
        - 가격 범위, 할인율, 재고 상태, 가격 추세 조건
        - JSON 스키마 검증
        - 조건 우선순위 설정
    
    Example:
        builder = AlertConditionBuilder()
        builder.add_price_condition(min_price=50000, max_price=100000)
        builder.add_discount_condition(min_discount=30)
        builder.add_trend_condition(trend='falling', threshold=10.0)
        conditions = builder.build()
    """
    
    # 지원하는 조건 타입
    CONDITION_TYPES = {
        'price': ['priceBelow', 'priceAbove', 'priceRange'],
        'discount': ['discountAtLeast', 'discountRange'],
        'stock': ['in_stock_only', 'out_of_stock_alert'],
        'trend': ['price_trend', 'price_drop_threshold', 'price_spike_threshold'],
        'relative_price': ['below_avg_price_percent', 'below_min_price_percent'],
        'attributes': ['category_attributes'],  # 카테고리별 속성 조건
    }
    
    # 트렌드 타입
    TREND_TYPES = ['falling', 'rising', 'stable', 'volatile']
    
    def __init__(self):
        self.conditions: Dict[str, Any] = {}
        self.operator = 'AND'  # AND | OR
        self.priority = 1  # 1 (최고) ~ 5 (최저)
        self.sub_conditions: List[Dict] = []
    
    def set_operator(self, operator: str):
        """논리 연산자 설정
        
        Args:
            operator: 'AND' | 'OR'
        """
        if operator not in ['AND', 'OR']:
            raise ValueError("Operator must be 'AND' or 'OR'")
        self.operator = operator
        return self
    
    def set_priority(self, priority: int):
        """우선순위 설정 (1=최고, 5=최저)"""
        if not 1 <= priority <= 5:
            raise ValueError("Priority must be between 1 and 5")
        self.priority = priority
        return self
    
    def add_price_condition(
        self,
        min_price: Optional[Decimal] = None,
        max_price: Optional[Decimal] = None,
        exact_price: Optional[Decimal] = None
    ):
        """가격 조건 추가
        
        Args:
            min_price: 최소 가격
            max_price: 최대 가격  
            exact_price: 정확한 가격 (테스트용)
        """
        if exact_price is not None:
            self.conditions['priceBelow'] = float(exact_price)
        elif min_price is not None and max_price is not None:
            self.conditions['priceRange'] = {
                'min': float(min_price),
                'max': float(max_price)
            }
        elif max_price is not None:
            self.conditions['priceBelow'] = float(max_price)
        elif min_price is not None:
            self.conditions['priceAbove'] = float(min_price)
        
        return self
    
    def add_discount_condition(
        self,
        min_discount: Optional[float] = None,
        max_discount: Optional[float] = None
    ):
        """할인율 조건 추가
        
        Args:
            min_discount: 최소 할인율 (%)
            max_discount: 최대 할인율 (%)
        """
        if min_discount is not None and max_discount is not None:
            self.conditions['discountRange'] = {
                'min': min_discount,
                'max': max_discount
            }
        elif min_discount is not None:
            self.conditions['discountAtLeast'] = min_discount
        
        return self
    
    def add_stock_condition(self, in_stock_only: bool = True, restock_alert: bool = False):
        """재고 조건 추가
        
        Args:
            in_stock_only: 재고 있는 상품만
            restock_alert: 재입고 알림 활성화
        """
        self.conditions['in_stock_only'] = in_stock_only
        self.conditions['out_of_stock_alert'] = restock_alert
        return self
    
    def add_trend_condition(
        self,
        trend: Optional[str] = None,
        threshold: Optional[float] = None
    ):
        """가격 추세 조건 추가
        
        Args:
            trend: 'falling' | 'rising' | 'stable' | 'volatile'
            threshold: 가격 변동률 임계값 (%)
        """
        if trend is not None:
            if trend not in self.TREND_TYPES:
                raise ValueError(f"Invalid trend type: {trend}")
            self.conditions['price_trend'] = trend
        
        if threshold is not None:
            if trend == 'falling':
                self.conditions['price_drop_threshold'] = threshold
            elif trend == 'rising':
                self.conditions['price_spike_threshold'] = threshold
        
        return self
    
    def add_relative_price_condition(
        self,
        below_avg_percent: Optional[float] = None,
        below_min_percent: Optional[float] = None
    ):
        """상대 가격 조건 추가
        
        Args:
            below_avg_percent: 평균가 대비 % 이하
            below_min_percent: 최저가 대비 % 이하
        """
        if below_avg_percent is not None:
            self.conditions['below_avg_price_percent'] = below_avg_percent
        
        if below_min_percent is not None:
            self.conditions['below_min_price_percent'] = below_min_percent
        
        return self
    
    def add_category_attribute(self, attribute: str, value: Any):
        """카테고리별 속성 조건 추가
        
        Args:
            attribute: 속성명 (downRatio, fillPowerMin, hood 등)
            value: 속성값
        """
        if 'category_attributes' not in self.conditions:
            self.conditions['category_attributes'] = {}
        
        self.conditions['category_attributes'][attribute] = value
        return self
    
    def add_sub_condition(self, sub_builder: 'AlertConditionBuilder'):
        """서브 조건 추가 (중첩 조건)
        
        Args:
            sub_builder: 하위 AlertConditionBuilder 인스턴스
        """
        self.sub_conditions.append(sub_builder.build())
        return self
    
    def build(self) -> Dict[str, Any]:
        """조건 빌드 및 검증
        
        Returns:
            검증된 조건 딕셔너리
        """
        result = {
            'conditions': self.conditions.copy(),
            'operator': self.operator,
            'priority': self.priority,
        }
        
        # 서브 조건 추가
        if self.sub_conditions:
            result['sub_conditions'] = self.sub_conditions
        
        # 유효성 검증
        self._validate_conditions(result)
        
        return result
    
    def _validate_conditions(self, conditions: Dict[str, Any]):
        """조건 유효성 검증
        
        Args:
            conditions: 검증할 조건 딕셔너리
        
        Raises:
            ValueError: 유효하지 않은 조건
        """
        cond = conditions.get('conditions', {})
        
        # 가격 범위 검증
        if 'priceRange' in cond:
            price_range = cond['priceRange']
            if price_range['min'] >= price_range['max']:
                raise ValueError("min_price must be less than max_price")
        
        # 할인율 범위 검증
        if 'discountRange' in cond:
            discount_range = cond['discountRange']
            if not 0 <= discount_range['min'] <= 100:
                raise ValueError("min_discount must be between 0 and 100")
            if not 0 <= discount_range['max'] <= 100:
                raise ValueError("max_discount must be between 0 and 100")
            if discount_range['min'] >= discount_range['max']:
                raise ValueError("min_discount must be less than max_discount")
        
        # 단일 할인율 검증
        if 'discountAtLeast' in cond:
            if not 0 <= cond['discountAtLeast'] <= 100:
                raise ValueError("discountAtLeast must be between 0 and 100")
        
        # 추세 임계값 검증
        if 'price_drop_threshold' in cond:
            if cond['price_drop_threshold'] <= 0:
                raise ValueError("price_drop_threshold must be positive")
        
        if 'price_spike_threshold' in cond:
            if cond['price_spike_threshold'] <= 0:
                raise ValueError("price_spike_threshold must be positive")
        
        logger.debug(f"Conditions validated: {conditions}")
    
    @staticmethod
    def from_dict(data: Dict[str, Any]) -> 'AlertConditionBuilder':
        """딕셔너리에서 빌더 생성
        
        Args:
            data: 조건 딕셔너리
        
        Returns:
            AlertConditionBuilder 인스턴스
        """
        builder = AlertConditionBuilder()
        
        # 연산자 및 우선순위
        builder.operator = data.get('operator', 'AND')
        builder.priority = data.get('priority', 1)
        
        # 조건 추가
        cond = data.get('conditions', {})
        
        # 가격 조건
        if 'priceBelow' in cond:
            builder.add_price_condition(max_price=Decimal(str(cond['priceBelow'])))
        elif 'priceAbove' in cond:
            builder.add_price_condition(min_price=Decimal(str(cond['priceAbove'])))
        elif 'priceRange' in cond:
            builder.add_price_condition(
                min_price=Decimal(str(cond['priceRange']['min'])),
                max_price=Decimal(str(cond['priceRange']['max']))
            )
        
        # 할인 조건
        if 'discountAtLeast' in cond:
            builder.add_discount_condition(min_discount=cond['discountAtLeast'])
        elif 'discountRange' in cond:
            builder.add_discount_condition(
                min_discount=cond['discountRange']['min'],
                max_discount=cond['discountRange']['max']
            )
        
        # 재고 조건
        if 'in_stock_only' in cond or 'out_of_stock_alert' in cond:
            builder.add_stock_condition(
                in_stock_only=cond.get('in_stock_only', True),
                restock_alert=cond.get('out_of_stock_alert', False)
            )
        
        # 추세 조건
        if 'price_trend' in cond:
            threshold = None
            trend = cond['price_trend']
            
            if trend == 'falling' and 'price_drop_threshold' in cond:
                threshold = cond['price_drop_threshold']
            elif trend == 'rising' and 'price_spike_threshold' in cond:
                threshold = cond['price_spike_threshold']
            
            builder.add_trend_condition(trend=trend, threshold=threshold)
        
        # 상대 가격 조건
        if 'below_avg_price_percent' in cond:
            builder.add_relative_price_condition(
                below_avg_percent=cond['below_avg_price_percent']
            )
        if 'below_min_price_percent' in cond:
            builder.add_relative_price_condition(
                below_min_percent=cond['below_min_price_percent']
            )
        
        # 카테고리 속성
        if 'category_attributes' in cond:
            for attr, value in cond['category_attributes'].items():
                builder.add_category_attribute(attr, value)
        
        # 서브 조건
        if 'sub_conditions' in data:
            for sub_cond in data['sub_conditions']:
                sub_builder = AlertConditionBuilder.from_dict(sub_cond)
                builder.add_sub_condition(sub_builder)
        
        return builder
    
    @staticmethod
    def validate_schema(conditions: Dict[str, Any]) -> bool:
        """조건 스키마 검증 (외부 입력 검증용)
        
        Args:
            conditions: 검증할 조건 딕셔너리
        
        Returns:
            유효 여부
        
        Raises:
            ValueError: 유효하지 않은 스키마
        """
        try:
            builder = AlertConditionBuilder.from_dict(conditions)
            builder.build()  # 빌드 시 검증 실행
            return True
        except Exception as e:
            logger.error(f"Condition schema validation failed: {e}")
            raise ValueError(f"Invalid condition schema: {e}")
