"""
Advanced Alert Views
고급 알림 관리 API
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.db.models import Count, Avg, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal
import logging

from apps.alerts.models import Alert, AlertHistory, AlertStatistics, EmailQueue
from apps.alerts.serializers import AlertSerializer
from apps.alerts.services import (
    AlertConditionBuilder,
    PriceTrendAnalyzer,
    SmartAlertMatcher
)

logger = logging.getLogger(__name__)


class AlertDashboardAPIView(APIView):
    """알림 대시보드 API
    
    Endpoint: GET /api/alerts/dashboard/?email={email}
    
    Returns:
        - 활성 알림 목록
        - 알림 통계 (발송 수, 클릭 수, 클릭률)
        - 최근 매칭 이력
    """
    
    def get(self, request):
        email = request.GET.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 활성 알림 조회
        active_alerts = Alert.objects.filter(
            email=email,
            active=True
        ).select_related('brand', 'category')
        
        # 비활성 알림 수
        inactive_count = Alert.objects.filter(
            email=email,
            active=False
        ).count()
        
        # 알림 통계 (최근 30일)
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        alert_ids = list(active_alerts.values_list('id', flat=True))
        
        # 통계 집계
        stats = AlertHistory.objects.filter(
            alert_id__in=alert_ids,
            created_at__gte=thirty_days_ago
        ).aggregate(
            total_matched=Count('id'),
            total_sent=Count('id', filter=Q(email_sent=True)),
            total_clicked=Count('id', filter=Q(clicked=True))
        )
        
        total_matched = stats['total_matched'] or 0
        total_sent = stats['total_sent'] or 0
        total_clicked = stats['total_clicked'] or 0
        
        click_rate = (total_clicked / total_sent * 100) if total_sent > 0 else 0
        
        # 최근 매칭 이력 (5개)
        recent_history = AlertHistory.objects.filter(
            alert_id__in=alert_ids
        ).order_by('-created_at')[:5]
        
        history_data = [
            {
                'product_id': h.product_id,
                'product_title': h.product_data.get('title', ''),
                'price': h.product_data.get('price', 0),
                'matched_at': h.created_at.isoformat(),
                'email_sent': h.email_sent,
                'clicked': h.clicked,
            }
            for h in recent_history
        ]
        
        # 응답 데이터
        return Response({
            'alerts': AlertSerializer(active_alerts, many=True).data,
            'inactive_alerts_count': inactive_count,
            'statistics': {
                'total_matched': total_matched,
                'total_sent': total_sent,
                'total_clicked': total_clicked,
                'click_rate': round(click_rate, 2),
                'period_days': 30,
            },
            'recent_history': history_data,
        })


class AlertHistoryAPIView(APIView):
    """알림 히스토리 API
    
    Endpoint: GET /api/alerts/{alert_id}/history/
    
    Query Parameters:
        - limit: 결과 수 (기본 20)
        - offset: 오프셋
    """
    
    def get(self, request, alert_id):
        limit = int(request.GET.get('limit', 20))
        offset = int(request.GET.get('offset', 0))
        
        # 알림 존재 확인
        try:
            alert = Alert.objects.get(id=alert_id)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 히스토리 조회
        history = AlertHistory.objects.filter(
            alert=alert
        ).order_by('-created_at')[offset:offset+limit]
        
        total = AlertHistory.objects.filter(alert=alert).count()
        
        # 데이터 변환
        history_data = [
            {
                'id': str(h.id),
                'product_id': h.product_id,
                'product_data': h.product_data,
                'matched_conditions': h.matched_conditions,
                'priority': h.priority,
                'email_sent': h.email_sent,
                'email_sent_at': h.email_sent_at.isoformat() if h.email_sent_at else None,
                'clicked': h.clicked,
                'clicked_at': h.clicked_at.isoformat() if h.clicked_at else None,
                'created_at': h.created_at.isoformat(),
            }
            for h in history
        ]
        
        return Response({
            'history': history_data,
            'total': total,
            'limit': limit,
            'offset': offset,
        })


class AlertStatisticsAPIView(APIView):
    """알림 통계 API
    
    Endpoint: GET /api/alerts/{alert_id}/statistics/
    
    Query Parameters:
        - days: 통계 기간 (기본 30일)
    """
    
    def get(self, request, alert_id):
        days = int(request.GET.get('days', 30))
        
        # 알림 존재 확인
        try:
            alert = Alert.objects.get(id=alert_id)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 기간 설정
        end_date = timezone.now().date()
        start_date = end_date - timedelta(days=days)
        
        # 통계 조회
        stats = AlertStatistics.objects.filter(
            alert=alert,
            date__gte=start_date,
            date__lte=end_date
        ).order_by('date')
        
        # 일별 데이터
        daily_data = [
            {
                'date': s.date.isoformat(),
                'matched': s.total_matched,
                'sent': s.total_sent,
                'clicked': s.total_clicked,
                'click_rate': s.click_rate,
                'avg_price': float(s.avg_matched_price) if s.avg_matched_price else None,
                'avg_discount': s.avg_discount_rate,
            }
            for s in stats
        ]
        
        # 전체 요약
        summary = stats.aggregate(
            total_matched=Count('total_matched'),
            total_sent=Count('total_sent'),
            total_clicked=Count('total_clicked'),
            avg_click_rate=Avg('click_rate'),
            avg_price=Avg('avg_matched_price'),
        )
        
        return Response({
            'alert_id': str(alert_id),
            'period': {
                'start_date': start_date.isoformat(),
                'end_date': end_date.isoformat(),
                'days': days,
            },
            'summary': {
                'total_matched': summary['total_matched'] or 0,
                'total_sent': summary['total_sent'] or 0,
                'total_clicked': summary['total_clicked'] or 0,
                'avg_click_rate': round(summary['avg_click_rate'] or 0, 2),
                'avg_price': float(summary['avg_price']) if summary['avg_price'] else None,
            },
            'daily': daily_data,
        })


class AlertConditionValidateAPIView(APIView):
    """알림 조건 검증 API
    
    Endpoint: POST /api/alerts/validate-conditions/
    
    Request Body:
        {
            "conditions": {...},
            "operator": "AND",
            "priority": 1
        }
    """
    
    def post(self, request):
        try:
            conditions = request.data
            
            # 조건 검증
            AlertConditionBuilder.validate_schema(conditions)
            
            return Response({
                'valid': True,
                'message': 'Conditions are valid'
            })
            
        except ValueError as e:
            return Response(
                {
                    'valid': False,
                    'error': str(e)
                },
                status=status.HTTP_400_BAD_REQUEST
            )


class ProductTrendAPIView(APIView):
    """상품 가격 추세 API
    
    Endpoint: GET /api/products/{product_id}/trend/
    
    Query Parameters:
        - days: 분석 기간 (기본 30일)
    """
    
    def get(self, request, product_id):
        days = int(request.GET.get('days', 30))
        
        analyzer = PriceTrendAnalyzer()
        
        try:
            # 추세 분석
            trend = analyzer.analyze_product_trend(product_id, period_days=days)
            
            # 가격 이력 데이터
            history_data = analyzer.get_price_history_data(product_id, period_days=days)
            
            # 데이터 변환
            history_formatted = [
                {
                    'date': dt.isoformat(),
                    'price': price
                }
                for dt, price in history_data
            ]
            
            return Response({
                'product_id': product_id,
                'trend': trend,
                'history': history_formatted,
            })
            
        except Exception as e:
            logger.error(f"Failed to analyze trend for {product_id}: {e}")
            return Response(
                {'error': 'Failed to analyze product trend'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AlertBulkUpdateAPIView(APIView):
    """알림 일괄 업데이트 API
    
    Endpoint: POST /api/alerts/bulk-update/
    
    Request Body:
        {
            "email": "user@example.com",
            "action": "activate" | "deactivate" | "delete",
            "alert_ids": [...]
        }
    """
    
    def post(self, request):
        email = request.data.get('email')
        action = request.data.get('action')
        alert_ids = request.data.get('alert_ids', [])
        
        if not email or not action:
            return Response(
                {'error': 'Email and action are required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 알림 조회
        alerts = Alert.objects.filter(
            id__in=alert_ids,
            email=email
        )
        
        if not alerts.exists():
            return Response(
                {'error': 'No alerts found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        # 액션 실행
        updated_count = 0
        
        if action == 'activate':
            updated_count = alerts.update(active=True)
        elif action == 'deactivate':
            updated_count = alerts.update(active=False)
        elif action == 'delete':
            updated_count, _ = alerts.delete()
        else:
            return Response(
                {'error': 'Invalid action'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        return Response({
            'action': action,
            'updated_count': updated_count,
        })


class RecommendedAlertsAPIView(APIView):
    """추천 알림 조건 API
    
    Endpoint: GET /api/alerts/recommended/?email={email}
    
    사용자의 구매 히스토리 및 알림 히스토리 기반 추천
    """
    
    def get(self, request):
        email = request.GET.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 사용자 알림 히스토리 분석
        alert_ids = Alert.objects.filter(email=email).values_list('id', flat=True)
        
        # 클릭한 상품 분석
        clicked_history = AlertHistory.objects.filter(
            alert_id__in=alert_ids,
            clicked=True
        ).order_by('-clicked_at')[:10]
        
        # 평균 가격대 계산
        prices = [h.product_data.get('price', 0) for h in clicked_history]
        avg_price = sum(prices) / len(prices) if prices else 100000
        
        # 평균 할인율 계산
        discounts = [h.product_data.get('discount_rate', 0) for h in clicked_history]
        avg_discount = sum(discounts) / len(discounts) if discounts else 30
        
        # 추천 조건 생성
        recommended_conditions = []
        
        # 1. 가격 기반 추천
        builder1 = AlertConditionBuilder()
        builder1.add_price_condition(
            min_price=Decimal(avg_price * 0.7),
            max_price=Decimal(avg_price * 1.3)
        )
        builder1.add_discount_condition(min_discount=avg_discount)
        builder1.set_priority(1)
        
        recommended_conditions.append({
            'name': '선호 가격대',
            'description': f'{int(avg_price * 0.7):,}원 ~ {int(avg_price * 1.3):,}원, {int(avg_discount)}% 이상 할인',
            'conditions': builder1.build()
        })
        
        # 2. 추세 기반 추천 (가격 하락)
        builder2 = AlertConditionBuilder()
        builder2.add_trend_condition(trend='falling', threshold=10.0)
        builder2.add_stock_condition(in_stock_only=True)
        builder2.set_priority(2)
        
        recommended_conditions.append({
            'name': '가격 하락 추세',
            'description': '최근 7일간 10% 이상 가격 하락한 상품',
            'conditions': builder2.build()
        })
        
        # 3. 재입고 알림
        builder3 = AlertConditionBuilder()
        builder3.add_stock_condition(in_stock_only=False, restock_alert=True)
        builder3.set_priority(3)
        
        recommended_conditions.append({
            'name': '재입고 알림',
            'description': '품절 상품이 다시 입고될 때 알림',
            'conditions': builder3.build()
        })
        
        return Response({
            'email': email,
            'recommended': recommended_conditions,
            'based_on': {
                'clicked_products': len(clicked_history),
                'avg_price': round(avg_price, 2),
                'avg_discount': round(avg_discount, 2),
            }
        })
