"""
FAISS 인덱스 재구축 명령어 (GenericProduct용)

Usage:
    python manage.py rebuild_faiss_index
    python manage.py rebuild_faiss_index --limit 100
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from apps.products.models import GenericProduct
from apps.recommendations.models import ImageEmbedding
from apps.recommendations.services.faiss_manager import FaissIndexManager
import numpy as np
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Rebuild Faiss index from existing ImageEmbedding records (GenericProduct)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of embeddings to index (for testing)'
        )
        parser.add_argument(
            '--model-version',
            type=str,
            default='resnet50',
            help='Model version to use (default: resnet50)'
        )

    def handle(self, *args, **options):
        limit = options.get('limit')
        model_version = options['model_version']
        
        self.stdout.write(self.style.SUCCESS(
            f'\n=== FAISS 인덱스 재구축 ==='
        ))
        self.stdout.write(f'모델 버전: {model_version}')
        if limit:
            self.stdout.write(f'제한: {limit}개')
        
        start_time = timezone.now()
        
        # 1. 기존 임베딩 조회
        self.stdout.write('\n[1단계] 데이터베이스 임베딩 조회')
        self.stdout.write('-' * 60)
        
        query = ImageEmbedding.objects.filter(model_version=model_version)
        
        if limit:
            query = query[:limit]
        
        all_embeddings = list(query)
        total_embeddings = len(all_embeddings)
        
        self.stdout.write(f'  DB 임베딩 개수: {total_embeddings}개')
        
        if total_embeddings == 0:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  임베딩이 없습니다!'
            ))
            self.stdout.write('해결방법: python manage.py generate_embeddings 실행')
            return
        
        # 2. 벡터와 상품 ID 준비
        self.stdout.write('\n[2단계] 벡터 데이터 준비')
        self.stdout.write('-' * 60)
        
        vectors = []
        product_ids = []
        valid_count = 0
        invalid_count = 0
        
        for i, embedding in enumerate(all_embeddings, 1):
            if i % 100 == 0 or i == total_embeddings:
                self.stdout.write(f'  처리 중... {i}/{total_embeddings}', ending='\r')
            
            try:
                # 임베딩 벡터 변환
                vec = np.array(embedding.embedding_vector, dtype=np.float32)
                
                # 차원 확인
                if len(vec) != 2048:
                    self.stdout.write(
                        self.style.WARNING(
                            f'\n  ⚠️  잘못된 차원: {embedding.product_id} (차원={len(vec)})'
                        )
                    )
                    invalid_count += 1
                    continue
                
                vectors.append(vec)
                product_ids.append(embedding.product_id)
                valid_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(
                        f'\n  ✗ 오류: {embedding.product_id} - {str(e)}'
                    )
                )
                invalid_count += 1
        
        self.stdout.write('')  # 줄바꿈
        self.stdout.write(f'  유효한 벡터: {valid_count}개')
        if invalid_count > 0:
            self.stdout.write(
                self.style.WARNING(f'  무효한 벡터: {invalid_count}개')
            )
        
        if valid_count == 0:
            self.stdout.write(self.style.ERROR('\n❌ 유효한 벡터가 없습니다'))
            return
        
        # NumPy 배열로 변환
        vectors = np.array(vectors, dtype=np.float32)
        
        # 3. FAISS 인덱스 재구축
        self.stdout.write('\n[3단계] FAISS 인덱스 재구축')
        self.stdout.write('-' * 60)
        
        try:
            faiss_manager = FaissIndexManager()
            
            # 기존 인덱스 초기화
            self.stdout.write('  기존 인덱스 초기화...')
            faiss_manager.reset()
            
            # 새 벡터 추가
            self.stdout.write(f'  {valid_count}개 벡터 추가...')
            success = faiss_manager.add_vectors(vectors, product_ids)
            
            if not success:
                self.stdout.write(self.style.ERROR('  ✗ 벡터 추가 실패'))
                return
            
            self.stdout.write(self.style.SUCCESS('  ✓ 벡터 추가 완료'))
            
            # 인덱스 저장
            self.stdout.write('  인덱스 파일 저장...')
            save_success = faiss_manager.save()
            
            if save_success:
                self.stdout.write(self.style.SUCCESS('  ✓ 인덱스 저장 완료'))
            else:
                self.stdout.write(self.style.ERROR('  ✗ 인덱스 저장 실패'))
                return
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'\n✗ FAISS 인덱스 구축 실패: {str(e)}')
            )
            logger.error(f'Error building Faiss index: {str(e)}', exc_info=True)
            return
        
        # 4. 인덱스 검증
        self.stdout.write('\n[4단계] 인덱스 검증')
        self.stdout.write('-' * 60)
        
        stats = faiss_manager.get_stats()
        
        self.stdout.write(f'  총 벡터 수: {stats["total_vectors"]}')
        self.stdout.write(f'  벡터 차원: {stats["dimension"]}')
        self.stdout.write(f'  상품 개수: {stats["product_count"]}')
        self.stdout.write(f'  인덱스 타입: {stats["index_type"]}')
        
        # 검증: 인덱스와 매핑 일치 확인
        if stats["total_vectors"] != stats["product_count"]:
            self.stdout.write(
                self.style.WARNING(
                    f'\n⚠️  경고: 벡터 수({stats["total_vectors"]})와 '
                    f'상품 수({stats["product_count"]}) 불일치'
                )
            )
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ 인덱스 일관성 확인'))
        
        # 5. 최종 통계
        elapsed = timezone.now() - start_time
        elapsed_seconds = elapsed.total_seconds()
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write(self.style.SUCCESS('✅ FAISS 인덱스 재구축 완료!'))
        self.stdout.write('=' * 60)
        
        self.stdout.write(f'\n총 처리: {total_embeddings}개')
        self.stdout.write(self.style.SUCCESS(f'성공: {valid_count}개'))
        if invalid_count > 0:
            self.stdout.write(self.style.WARNING(f'실패: {invalid_count}개'))
        self.stdout.write(f'소요 시간: {elapsed_seconds:.1f}초')
        
        # 테스트 검색 수행
        self.stdout.write('\n[테스트 검색]')
        self.stdout.write('-' * 60)
        
        try:
            # 첫 번째 벡터로 검색 테스트
            test_vector = vectors[0]
            test_product_id = product_ids[0]
            
            self.stdout.write(f'테스트 상품: {test_product_id}')
            
            results = faiss_manager.search(
                query_vector=test_vector,
                k=5,
                exclude_product_id=test_product_id
            )
            
            if results:
                self.stdout.write(f'\n유사 상품 {len(results)}개 발견:')
                for i, result in enumerate(results, 1):
                    similarity_pct = result['similarity'] * 100
                    self.stdout.write(
                        f'  {i}. {result["product_id"]} '
                        f'(유사도: {similarity_pct:.1f}%)'
                    )
                self.stdout.write(self.style.SUCCESS('\n✓ 검색 기능 정상 작동'))
            else:
                self.stdout.write(self.style.WARNING('검색 결과 없음'))
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ 테스트 검색 실패: {str(e)}')
            )
        
        self.stdout.write('\n' + '=' * 60)
        self.stdout.write('이제 유사 상품 추천 API를 사용할 수 있습니다!')
        self.stdout.write('API: /api/recommendations/similar-images/<product_id>/')
        self.stdout.write('=' * 60 + '\n')
