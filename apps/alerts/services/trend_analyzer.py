"""
Price Trend Analyzer
가격 추세 분석 및 예측
"""
from typing import Dict, List, Optional, Tuple
from decimal import Decimal
from datetime import datetime, timedelta
from django.utils import timezone
from django.db.models import Avg, Min, Max, Count, Q
import logging

logger = logging.getLogger(__name__)


class PriceTrendAnalyzer:
    """가격 추세 분석기
    
    Features:
        - 7일/30일/90일 가격 추세 분석
        - 급등/급락 감지 (변동률 기반)
        - 평균가/최저가/최고가 계산
        - 가격 변동성 (Volatility) 계산
        - 추세 예측 (단순 선형 회귀)
    
    Usage:
        analyzer = PriceTrendAnalyzer()
        trend = analyzer.analyze_product_trend(product_id, period_days=30)
    """
    
    # 추세 타입
    TREND_FALLING = 'falling'  # 하락세
    TREND_RISING = 'rising'    # 상승세
    TREND_STABLE = 'stable'    # 안정세
    TREND_VOLATILE = 'volatile'  # 변동성 높음
    
    # 추세 판단 임계값
    THRESHOLD_STABLE = 3.0  # 변동률 3% 이하: 안정
    THRESHOLD_FALLING = -5.0  # 변동률 -5% 이하: 하락
    THRESHOLD_RISING = 5.0  # 변동률 5% 이상: 상승
    THRESHOLD_VOLATILE = 10.0  # 표준편차 10% 이상: 변동성
    
    def __init__(self):
        self.cache = {}  # 간단한 캐싱
    
    def analyze_product_trend(
        self,
        product_id: str,
        period_days: int = 30
    ) -> Dict[str, any]:
        """상품 가격 추세 분석
        
        Args:
            product_id: 상품 ID
            period_days: 분석 기간 (일)
        
        Returns:
            추세 분석 결과
            {
                'trend': 'falling' | 'rising' | 'stable' | 'volatile',
                'avg_price': 평균 가격,
                'min_price': 최저 가격,
                'max_price': 최고 가격,
                'current_price': 현재 가격,
                'price_change': 가격 변동액,
                'price_change_percent': 가격 변동률 (%),
                'volatility': 변동성 (표준편차),
                'data_points': 데이터 포인트 수,
                'period_start': 분석 시작일,
                'period_end': 분석 종료일,
            }
        """
        from apps.products.models import PriceHistory
        
        # 캐시 체크 (1분 TTL)
        cache_key = f"{product_id}:{period_days}"
        if cache_key in self.cache:
            cached_time, cached_data = self.cache[cache_key]
            if (timezone.now() - cached_time).seconds < 60:
                return cached_data
        
        # 기간 설정
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        # 가격 이력 조회
        price_history = PriceHistory.objects.filter(
            product_id=product_id,
            recorded_at__gte=start_date,
            recorded_at__lte=end_date
        ).order_by('recorded_at')
        
        if not price_history.exists():
            logger.warning(f"No price history found for product {product_id}")
            return self._empty_trend_result(product_id)
        
        # 통계 계산
        stats = price_history.aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price'),
            count=Count('id')
        )
        
        # 가격 리스트
        prices = list(price_history.values_list('price', flat=True))
        prices_float = [float(p) for p in prices]
        
        # 첫 가격, 마지막 가격
        first_price = prices_float[0]
        last_price = prices_float[-1]
        
        # 변동 계산
        price_change = last_price - first_price
        price_change_percent = (price_change / first_price) * 100 if first_price > 0 else 0
        
        # 변동성 (표준편차)
        volatility = self._calculate_volatility(prices_float)
        
        # 추세 판단
        trend = self._determine_trend(price_change_percent, volatility)
        
        result = {
            'trend': trend,
            'avg_price': float(stats['avg_price']),
            'min_price': float(stats['min_price']),
            'max_price': float(stats['max_price']),
            'current_price': last_price,
            'price_change': price_change,
            'price_change_percent': price_change_percent,
            'volatility': volatility,
            'data_points': stats['count'],
            'period_start': start_date.isoformat(),
            'period_end': end_date.isoformat(),
        }
        
        # 캐싱
        self.cache[cache_key] = (timezone.now(), result)
        
        return result
    
    def detect_price_spike(
        self,
        product_id: str,
        threshold_percent: float = 10.0,
        period_days: int = 7
    ) -> Optional[Dict]:
        """가격 급등 감지
        
        Args:
            product_id: 상품 ID
            threshold_percent: 급등 임계값 (%)
            period_days: 감지 기간 (일)
        
        Returns:
            급등 정보 (없으면 None)
            {
                'detected': True,
                'price_change_percent': 변동률,
                'previous_price': 이전 가격,
                'current_price': 현재 가격,
                'spike_date': 급등 감지일
            }
        """
        from apps.products.models import PriceHistory
        
        # 최근 가격 이력
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        history = PriceHistory.objects.filter(
            product_id=product_id,
            recorded_at__gte=start_date
        ).order_by('-recorded_at')[:2]
        
        if history.count() < 2:
            return None
        
        current = history[0]
        previous = history[1]
        
        price_change = float(current.price) - float(previous.price)
        price_change_percent = (price_change / float(previous.price)) * 100
        
        if price_change_percent >= threshold_percent:
            return {
                'detected': True,
                'price_change_percent': price_change_percent,
                'previous_price': float(previous.price),
                'current_price': float(current.price),
                'spike_date': current.recorded_at.isoformat(),
            }
        
        return None
    
    def detect_price_drop(
        self,
        product_id: str,
        threshold_percent: float = 10.0,
        period_days: int = 7
    ) -> Optional[Dict]:
        """가격 급락 감지
        
        Args:
            product_id: 상품 ID
            threshold_percent: 급락 임계값 (%)
            period_days: 감지 기간 (일)
        
        Returns:
            급락 정보 (없으면 None)
        """
        from apps.products.models import PriceHistory
        
        # 최근 가격 이력
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        history = PriceHistory.objects.filter(
            product_id=product_id,
            recorded_at__gte=start_date
        ).order_by('-recorded_at')[:2]
        
        if history.count() < 2:
            return None
        
        current = history[0]
        previous = history[1]
        
        price_change = float(previous.price) - float(current.price)  # 하락은 양수
        price_change_percent = (price_change / float(previous.price)) * 100
        
        if price_change_percent >= threshold_percent:
            return {
                'detected': True,
                'price_change_percent': price_change_percent,
                'previous_price': float(previous.price),
                'current_price': float(current.price),
                'drop_date': current.recorded_at.isoformat(),
            }
        
        return None
    
    def calculate_relative_price(
        self,
        product_id: str,
        current_price: Decimal,
        period_days: int = 30
    ) -> Dict[str, float]:
        """상대 가격 계산 (평균가/최저가 대비)
        
        Args:
            product_id: 상품 ID
            current_price: 현재 가격
            period_days: 비교 기간 (일)
        
        Returns:
            {
                'vs_avg_percent': 평균가 대비 % (음수: 평균보다 저렴),
                'vs_min_percent': 최저가 대비 % (0 이상),
                'vs_max_percent': 최고가 대비 % (0 이하),
            }
        """
        from apps.products.models import PriceHistory
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        stats = PriceHistory.objects.filter(
            product_id=product_id,
            recorded_at__gte=start_date
        ).aggregate(
            avg_price=Avg('price'),
            min_price=Min('price'),
            max_price=Max('price')
        )
        
        if not stats['avg_price']:
            return {
                'vs_avg_percent': 0.0,
                'vs_min_percent': 0.0,
                'vs_max_percent': 0.0,
            }
        
        current = float(current_price)
        avg = float(stats['avg_price'])
        min_price = float(stats['min_price'])
        max_price = float(stats['max_price'])
        
        return {
            'vs_avg_percent': ((current - avg) / avg) * 100,
            'vs_min_percent': ((current - min_price) / min_price) * 100 if min_price > 0 else 0,
            'vs_max_percent': ((current - max_price) / max_price) * 100 if max_price > 0 else 0,
        }
    
    def get_price_history_data(
        self,
        product_id: str,
        period_days: int = 30
    ) -> List[Tuple[datetime, float]]:
        """가격 이력 데이터 조회 (그래프용)
        
        Args:
            product_id: 상품 ID
            period_days: 조회 기간 (일)
        
        Returns:
            [(날짜, 가격), ...] 리스트
        """
        from apps.products.models import PriceHistory
        
        end_date = timezone.now()
        start_date = end_date - timedelta(days=period_days)
        
        history = PriceHistory.objects.filter(
            product_id=product_id,
            recorded_at__gte=start_date
        ).order_by('recorded_at').values_list('recorded_at', 'price')
        
        return [(dt, float(price)) for dt, price in history]
    
    def _calculate_volatility(self, prices: List[float]) -> float:
        """변동성 계산 (표준편차)
        
        Args:
            prices: 가격 리스트
        
        Returns:
            변동성 (%)
        """
        if len(prices) < 2:
            return 0.0
        
        mean = sum(prices) / len(prices)
        variance = sum((p - mean) ** 2 for p in prices) / len(prices)
        std_dev = variance ** 0.5
        
        # 평균 대비 표준편차 비율
        volatility = (std_dev / mean) * 100 if mean > 0 else 0
        
        return volatility
    
    def _determine_trend(self, price_change_percent: float, volatility: float) -> str:
        """추세 판단
        
        Args:
            price_change_percent: 가격 변동률 (%)
            volatility: 변동성 (%)
        
        Returns:
            추세 타입
        """
        # 변동성이 높으면 volatile
        if volatility >= self.THRESHOLD_VOLATILE:
            return self.TREND_VOLATILE
        
        # 변동률에 따라 판단
        if price_change_percent <= self.THRESHOLD_FALLING:
            return self.TREND_FALLING
        elif price_change_percent >= self.THRESHOLD_RISING:
            return self.TREND_RISING
        else:
            return self.TREND_STABLE
    
    def _empty_trend_result(self, product_id: str) -> Dict:
        """빈 결과 반환 (데이터 없음)"""
        return {
            'trend': self.TREND_STABLE,
            'avg_price': 0.0,
            'min_price': 0.0,
            'max_price': 0.0,
            'current_price': 0.0,
            'price_change': 0.0,
            'price_change_percent': 0.0,
            'volatility': 0.0,
            'data_points': 0,
            'period_start': None,
            'period_end': None,
            'error': 'No price history found'
        }
    
    def batch_analyze_trends(
        self,
        product_ids: List[str],
        period_days: int = 30
    ) -> Dict[str, Dict]:
        """여러 상품 추세 일괄 분석
        
        Args:
            product_ids: 상품 ID 리스트
            period_days: 분석 기간
        
        Returns:
            {product_id: trend_result, ...}
        """
        results = {}
        
        for product_id in product_ids:
            try:
                results[product_id] = self.analyze_product_trend(product_id, period_days)
            except Exception as e:
                logger.error(f"Failed to analyze trend for {product_id}: {e}")
                results[product_id] = self._empty_trend_result(product_id)
        
        return results
