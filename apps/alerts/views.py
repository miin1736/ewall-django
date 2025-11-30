"""
Alert API views
"""
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from apps.alerts.models import Alert
from apps.alerts.serializers import AlertSerializer


class AlertCreateAPIView(APIView):
    """알림 생성 API
    
    Endpoint: POST /api/alerts/
    """
    
    def post(self, request):
        serializer = AlertSerializer(data=request.data)
        
        if serializer.is_valid():
            alert = serializer.save()
            return Response(
                AlertSerializer(alert).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )


class AlertListAPIView(APIView):
    """사용자 알림 목록 API
    
    Endpoint: GET /api/alerts/?email={email}
    """
    
    def get(self, request):
        email = request.GET.get('email')
        
        if not email:
            return Response(
                {'error': 'Email parameter is required'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        alerts = Alert.objects.filter(email=email).select_related('brand', 'category')
        serializer = AlertSerializer(alerts, many=True)
        
        return Response({
            'alerts': serializer.data,
            'total': alerts.count()
        })


class AlertUpdateAPIView(APIView):
    """알림 수정/삭제 API
    
    Endpoint: 
        PUT /api/alerts/{alert_id}/
        DELETE /api/alerts/{alert_id}/
    """
    
    def put(self, request, alert_id):
        try:
            alert = Alert.objects.get(id=alert_id)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
        
        serializer = AlertSerializer(alert, data=request.data, partial=True)
        
        if serializer.is_valid():
            alert = serializer.save()
            return Response(AlertSerializer(alert).data)
        
        return Response(
            serializer.errors,
            status=status.HTTP_400_BAD_REQUEST
        )
    
    def delete(self, request, alert_id):
        try:
            alert = Alert.objects.get(id=alert_id)
            alert.delete()
            return Response(status=status.HTTP_204_NO_CONTENT)
        except Alert.DoesNotExist:
            return Response(
                {'error': 'Alert not found'},
                status=status.HTTP_404_NOT_FOUND
            )
