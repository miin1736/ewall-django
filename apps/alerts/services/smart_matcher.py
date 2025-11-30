"""
Smart Alert Matcher
복합 조건 매칭 및 우선순위 기반 알림
"""
from typing import Dict, Any, List, Optional, Tuple
from decimal import Decimal
from django.db.models import Model
from django.utils import timezone
from datetime import timedelta
import logging

from .condition_builder import AlertConditionBuilder
from .trend_analyzer import PriceTrendAnalyzer

logger = logging.getLogger(__name__)


class SmartAlertMatcher:
    """스마트 알림 매칭
    
    Features:
        - 복합 조건 매칭 (AND/OR)
        - 우선순위 기반 알림 정렬
        - 중복 알림 방지 (24시간 쿨다운)
        - 추세 기반 조건 매칭
        - 상대 가격 조건 매칭
        - 재입고 감지
    
    Usage:
        matcher = SmartAlertMatcher()
        matched = matcher.match_product_to_alerts(product, alerts)
    """
    
    def __init__(self):
        self.trend_analyzer = PriceTrendAnalyzer()
        self.cooldown_cache = {}  # {(alert_id, product_id): last_sent_time}
    
    def match_product_to_alerts(
        self,
        product: Model,
        alerts: List[Model],
        cooldown_hours: int = 24
    ) -> List[Tuple[Model, int]]:
        """상품과 알림 조건 매칭
        
        Args:
            product: 상품 모델 인스턴스
            alerts: 알림 모델 리스트
            cooldown_hours: 중복 알림 방지 시간 (시간)
        
        Returns:
            [(alert, priority), ...] 매칭된 알림 및 우선순위 리스트 (우선순위 순 정렬)
        """
        matched_alerts = []
        
        for alert in alerts:
            # 브랜드/카테고리 필터
            if alert.brand_id != product.brand_id or alert.category_id != product.category_id:
                continue
            
            # 쿨다운 체크
            if self._is_in_cooldown(alert.id, product.id, cooldown_hours):
                logger.debug(f"Alert {alert.id} for product {product.id} is in cooldown")
                continue
            
            # 조건 매칭
            if self.matches_conditions(product, alert.conditions):
                # 우선순위 추출 (기본값: 3)
                priority = alert.conditions.get('priority', 3)
                matched_alerts.append((alert, priority))
        
        # 우선순위 순 정렬 (1=최고, 5=최저)
        matched_alerts.sort(key=lambda x: x[1])
        
        return matched_alerts
    
    def matches_conditions(self, product: Model, conditions: Dict[str, Any]) -> bool:
        """복합 조건 매칭
        
        Args:
            product: 상품 모델 인스턴스
            conditions: 조건 딕셔너리 (AlertConditionBuilder.build() 결과)
        
        Returns:
            매칭 여부
        """
        # 조건 추출
        cond = conditions.get('conditions', {})
        operator = conditions.get('operator', 'AND')
        sub_conditions = conditions.get('sub_conditions', [])
        
        # 메인 조건 평가
        main_result = self._evaluate_conditions(product, cond)
        
        # 서브 조건 평가
        if sub_conditions:
            sub_results = [
                self.matches_conditions(product, sub_cond)
                for sub_cond in sub_conditions
            ]
            
            # 연산자에 따라 결합
            if operator == 'AND':
                return main_result and all(sub_results)
            else:  # OR
                return main_result or any(sub_results)
        
        return main_result
    
    def _evaluate_conditions(self, product: Model, conditions: Dict[str, Any]) -> bool:
        """단일 조건 세트 평가
        
        Args:
            product: 상품 모델 인스턴스
            conditions: 조건 딕셔너리
        
        Returns:
            조건 만족 여부
        """
        # 1. 가격 조건
        if not self._check_price_conditions(product, conditions):
            return False
        
        # 2. 할인 조건
        if not self._check_discount_conditions(product, conditions):
            return False
        
        # 3. 재고 조건
        if not self._check_stock_conditions(product, conditions):
            return False
        
        # 4. 추세 조건
        if not self._check_trend_conditions(product, conditions):
            return False
        
        # 5. 상대 가격 조건
        if not self._check_relative_price_conditions(product, conditions):
            return False
        
        # 6. 카테고리 속성 조건
        if not self._check_category_attributes(product, conditions):
            return False
        
        return True
    
    def _check_price_conditions(self, product: Model, conditions: Dict) -> bool:
        """가격 조건 체크"""
        price = float(product.price)
        
        # priceBelow
        if 'priceBelow' in conditions:
            if price > conditions['priceBelow']:
                return False
        
        # priceAbove
        if 'priceAbove' in conditions:
            if price < conditions['priceAbove']:
                return False
        
        # priceRange
        if 'priceRange' in conditions:
            range_cond = conditions['priceRange']
            if not (range_cond['min'] <= price <= range_cond['max']):
                return False
        
        return True
    
    def _check_discount_conditions(self, product: Model, conditions: Dict) -> bool:
        """할인 조건 체크"""
        discount = float(product.discount_rate)
        
        # discountAtLeast
        if 'discountAtLeast' in conditions:
            if discount < conditions['discountAtLeast']:
                return False
        
        # discountRange
        if 'discountRange' in conditions:
            range_cond = conditions['discountRange']
            if not (range_cond['min'] <= discount <= range_cond['max']):
                return False
        
        return True
    
    def _check_stock_conditions(self, product: Model, conditions: Dict) -> bool:
        """재고 조건 체크"""
        # in_stock_only
        if conditions.get('in_stock_only', False):
            if not product.in_stock:
                return False
        
        # out_of_stock_alert (재입고 알림)
        if conditions.get('out_of_stock_alert', False):
            # 재입고 여부 확인 (이전에 품절이었는지 확인 필요)
            was_out_of_stock = self._was_out_of_stock_recently(product.id)
            if not (product.in_stock and was_out_of_stock):
                return False
        
        return True
    
    def _check_trend_conditions(self, product: Model, conditions: Dict) -> bool:
        """추세 조건 체크"""
        # price_trend
        if 'price_trend' in conditions:
            expected_trend = conditions['price_trend']
            
            # 추세 분석 (7일 기준)
            trend_result = self.trend_analyzer.analyze_product_trend(
                product_id=product.id,
                period_days=7
            )
            
            actual_trend = trend_result.get('trend')
            
            if actual_trend != expected_trend:
                return False
        
        # price_drop_threshold
        if 'price_drop_threshold' in conditions:
            threshold = conditions['price_drop_threshold']
            
            drop_result = self.trend_analyzer.detect_price_drop(
                product_id=product.id,
                threshold_percent=threshold,
                period_days=7
            )
            
            if not drop_result or not drop_result.get('detected'):
                return False
        
        # price_spike_threshold
        if 'price_spike_threshold' in conditions:
            threshold = conditions['price_spike_threshold']
            
            spike_result = self.trend_analyzer.detect_price_spike(
                product_id=product.id,
                threshold_percent=threshold,
                period_days=7
            )
            
            if not spike_result or not spike_result.get('detected'):
                return False
        
        return True
    
    def _check_relative_price_conditions(self, product: Model, conditions: Dict) -> bool:
        """상대 가격 조건 체크"""
        # below_avg_price_percent (평균가 대비 % 이하)
        if 'below_avg_price_percent' in conditions:
            threshold = conditions['below_avg_price_percent']
            
            relative = self.trend_analyzer.calculate_relative_price(
                product_id=product.id,
                current_price=product.price,
                period_days=30
            )
            
            vs_avg = relative.get('vs_avg_percent', 0)
            
            # 음수: 평균보다 저렴, threshold 이하여야 함
            if vs_avg > threshold:
                return False
        
        # below_min_price_percent (최저가 대비 % 이하)
        if 'below_min_price_percent' in conditions:
            threshold = conditions['below_min_price_percent']
            
            relative = self.trend_analyzer.calculate_relative_price(
                product_id=product.id,
                current_price=product.price,
                period_days=30
            )
            
            vs_min = relative.get('vs_min_percent', 0)
            
            # 0 이상, threshold 이하여야 함
            if vs_min > threshold:
                return False
        
        return True
    
    def _check_category_attributes(self, product: Model, conditions: Dict) -> bool:
        """카테고리별 속성 조건 체크 (기존 matcher 로직 재사용)"""
        from .matcher import AlertMatcher
        
        # category_attributes가 있으면 기존 매처로 검증
        if 'category_attributes' in conditions:
            attrs = conditions['category_attributes']
            matcher = AlertMatcher()
            
            # 기존 조건 형식으로 변환 후 매칭
            return matcher.matches(product, attrs)
        
        return True
    
    def _was_out_of_stock_recently(self, product_id: str, days: int = 7) -> bool:
        """최근 품절 상태였는지 확인
        
        Args:
            product_id: 상품 ID
            days: 확인 기간 (일)
        
        Returns:
            최근 품절 상태였으면 True
        """
        from apps.products.models import (
            DownProduct, SlacksProduct, JeansProduct,
            CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
        )
        
        # 모델 매핑 (간단히 GenericProduct로 시도)
        model_map = [
            DownProduct, SlacksProduct, JeansProduct,
            CrewneckProduct, LongSleeveProduct, CoatProduct, GenericProduct
        ]
        
        # 각 모델에서 조회
        threshold = timezone.now() - timedelta(days=days)
        
        for model in model_map:
            try:
                # 이전 기록 확인 (updated_at < 현재 시점)
                # 실제로는 PriceHistory에 in_stock 필드가 있어야 정확함
                # 간단히 현재 재고가 있고, 최근 업데이트가 있었다면 재입고로 간주
                product = model.objects.filter(id=product_id).first()
                
                if product:
                    # 최근 업데이트가 있고 재고가 있으면 재입고로 추정
                    if product.updated_at >= threshold and product.in_stock:
                        # 간단한 휴리스틱: 최근 업데이트 = 재입고 가능성
                        return True
                    break
            except:
                continue
        
        return False
    
    def _is_in_cooldown(self, alert_id: str, product_id: str, cooldown_hours: int) -> bool:
        """중복 알림 방지 쿨다운 체크
        
        Args:
            alert_id: 알림 ID
            product_id: 상품 ID
            cooldown_hours: 쿨다운 시간 (시간)
        
        Returns:
            쿨다운 중이면 True
        """
        cache_key = (str(alert_id), str(product_id))
        
        if cache_key in self.cooldown_cache:
            last_sent = self.cooldown_cache[cache_key]
            elapsed = timezone.now() - last_sent
            
            if elapsed < timedelta(hours=cooldown_hours):
                return True
        
        return False
    
    def mark_sent(self, alert_id: str, product_id: str):
        """알림 발송 기록 (쿨다운 시작)
        
        Args:
            alert_id: 알림 ID
            product_id: 상품 ID
        """
        cache_key = (str(alert_id), str(product_id))
        self.cooldown_cache[cache_key] = timezone.now()
    
    def batch_match_products(
        self,
        products: List[Model],
        alerts: List[Model],
        cooldown_hours: int = 24
    ) -> Dict[str, List[Tuple[Model, int]]]:
        """여러 상품 일괄 매칭
        
        Args:
            products: 상품 리스트
            alerts: 알림 리스트
            cooldown_hours: 쿨다운 시간
        
        Returns:
            {product_id: [(alert, priority), ...], ...}
        """
        results = {}
        
        for product in products:
            matched = self.match_product_to_alerts(product, alerts, cooldown_hours)
            
            if matched:
                results[product.id] = matched
        
        return results
    
    def clear_cooldown_cache(self):
        """쿨다운 캐시 초기화"""
        self.cooldown_cache.clear()
