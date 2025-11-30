"""
Management Command - Build Recommendation Index
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = '협업 필터링 추천 인덱스 빌드'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='분석할 최근 N일 (기본 30일)'
        )
        parser.add_argument(
            '--min-interactions',
            type=int,
            default=2,
            help='최소 상호작용 수 (기본 2)'
        )
    
    def handle(self, *args, **options):
        days = options['days']
        min_interactions = options['min_interactions']
        
        self.stdout.write(f"Building CF index (last {days} days, min {min_interactions} interactions)...")
        
        from apps.recommendations.services.collaborative_filter import CollaborativeFilter
        
        cf = CollaborativeFilter()
        stats = cf.build_similarity_matrix(
            days=days,
            min_interactions=min_interactions
        )
        
        if 'error' in stats:
            self.stdout.write(self.style.ERROR(f"Failed: {stats['error']}"))
            return
        
        self.stdout.write(self.style.SUCCESS("✓ CF index built successfully!"))
        self.stdout.write(f"  - Total interactions: {stats['total_interactions']}")
        self.stdout.write(f"  - Total users: {stats['total_users']}")
        self.stdout.write(f"  - Total products: {stats['total_products']}")
        self.stdout.write(f"  - Cached products: {stats['cached_products']}")
        self.stdout.write(f"  - Avg recommendations: {stats['avg_recommendations']}")
        self.stdout.write(f"  - Completed at: {stats['completed_at']}")
