import pytest
from django.utils import timezone
from apps.analytics.models import Click, DailyClickAggregate


@pytest.mark.unit
class TestClickModel:
    """Click 모델 단위 테스트"""
    
    def test_create_click(self, sample_click):
        """클릭 데이터 생성 테스트"""
        assert sample_click.user_identifier == 'test_user_1'
        assert sample_click.clicked_at is not None
    
    def test_click_product_association(self, sample_click, sample_down_product):
        """클릭 데이터와 상품 연결 테스트"""
        assert sample_click.product_code == sample_down_product.id
    
    def test_multiple_clicks_same_product(self, db, sample_down_product):
        """동일 상품에 대한 여러 클릭 테스트"""
        for i in range(5):
            Click.objects.create(
                product_code=sample_down_product.id,
                user_identifier=f'user_{i}',
                clicked_at=timezone.now()
            )
        
        clicks = Click.objects.filter(product_code=sample_down_product.id)
        assert clicks.count() == 5


@pytest.mark.unit
class TestDailyClickAggregateModel:
    """DailyClickAggregate 모델 단위 테스트"""
    
    def test_create_aggregate(self, db, sample_down_product):
        """일일 클릭 집계 생성 테스트"""
        from datetime import date
        
        aggregate = DailyClickAggregate.objects.create(
            product_code=sample_down_product.id,
            date=date.today(),
            click_count=10
        )
        
        assert aggregate.product_code == sample_down_product.id
        assert aggregate.click_count == 10
        assert aggregate.date == date.today()
    
    def test_aggregate_unique_constraint(self, db, sample_down_product):
        """일일 집계 유니크 제약조건 테스트"""
        from datetime import date
        from django.db import IntegrityError
        
        DailyClickAggregate.objects.create(
            product_code=sample_down_product.id,
            date=date.today(),
            click_count=5
        )
        
        # 같은 날짜, 같은 상품 코드로 중복 생성 시도
        with pytest.raises(IntegrityError):
            DailyClickAggregate.objects.create(
                product_code=sample_down_product.id,
                date=date.today(),
                click_count=10
            )
    
    def test_aggregate_click_count_increment(self, db, sample_down_product):
        """클릭 수 증가 테스트"""
        from datetime import date
        
        aggregate = DailyClickAggregate.objects.create(
            product_code=sample_down_product.id,
            date=date.today(),
            click_count=0
        )
        
        # 클릭 수 증가
        aggregate.click_count += 1
        aggregate.save()
        
        assert aggregate.click_count == 1
