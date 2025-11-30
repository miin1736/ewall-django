# P2-2: Image Similarity Recommendation System

## 개요
ResNet50과 Faiss를 활용한 이미지 기반 상품 추천 시스템입니다. 딥러닝을 통해 상품 이미지의 시각적 특징을 추출하고, 벡터 유사도 검색을 통해 비슷한 느낌의 상품을 추천합니다.

## 주요 기능
1. **이미지 특징 추출** (ResNet50)
   - ImageNet pre-trained 모델 활용
   - 2048차원 벡터 생성
   - L2 normalization 적용

2. **벡터 유사도 검색** (Faiss)
   - IndexFlatL2 (정확한 L2 distance)
   - K-NN 검색
   - 실시간 검색 성능

3. **API 엔드포인트**
   - 유사 이미지 검색
   - 인덱스 통계 조회

## 아키텍처

### 시스템 구성
```
┌─────────────────────────────────────────────────────────────┐
│                    Frontend Layer                           │
│  - similar_images.js (위젯)                                 │
│  - similar_images.css (스타일)                              │
│  - similar_images_widget.html (템플릿)                      │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP Request
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                     API Layer                               │
│  - SimilarImagesAPIView                                     │
│  - ImageIndexStatsAPIView                                   │
└────────────────────┬────────────────────────────────────────┘
                     │
                     ↓
┌─────────────────────────────────────────────────────────────┐
│                   Service Layer                             │
│  ┌────────────────────┐        ┌──────────────────────┐    │
│  │ ImageEmbeddingService      │ FaissIndexManager    │    │
│  │ - ResNet50 모델     │        │ - IndexFlatL2       │    │
│  │ - 이미지 전처리     │        │ - K-NN 검색         │    │
│  │ - 벡터 추출         │        │ - 인덱스 관리       │    │
│  └────────────────────┘        └──────────────────────┘    │
└────────────────────┬────────────────────┬───────────────────┘
                     │                    │
                     ↓                    ↓
┌─────────────────────────────────────────────────────────────┐
│                   Storage Layer                             │
│  ┌────────────────────┐        ┌──────────────────────┐    │
│  │ Django Cache       │        │ Faiss Index Files    │    │
│  │ (임베딩 캐시)      │        │ - image_index.faiss  │    │
│  └────────────────────┘        │ - product_mapping.pkl│    │
│                                │                      │    │
│  ┌────────────────────┐        └──────────────────────┘    │
│  │ PostgreSQL         │                                    │
│  │ - ImageEmbedding   │                                    │
│  └────────────────────┘                                    │
└─────────────────────────────────────────────────────────────┘
```

### 데이터 흐름
```
1. 이미지 업로드/URL
   ↓
2. ImageEmbeddingService
   - 이미지 다운로드
   - ResNet50으로 특징 추출
   - 2048-dim 벡터 생성
   ↓
3. 저장
   - ImageEmbedding 모델에 저장
   - Faiss 인덱스에 추가
   - 캐시에 저장 (1시간)
   ↓
4. 검색 시
   - Faiss에서 K-NN 검색
   - 유사도 계산 (1 / (1 + L2_distance))
   - 상품 정보와 결합하여 반환
```

## 구현 상세

### 1. ImageEmbeddingService
**파일**: `apps/recommendations/services/image_embedding.py`

#### 주요 메서드
```python
class ImageEmbeddingService:
    def __init__(self):
        """ResNet50 모델 초기화 (ImageNet pretrained)"""
        
    def get_embedding_from_url(url, use_cache=True):
        """
        URL에서 이미지 임베딩 생성
        - 캐시 확인 (1시간 TTL)
        - 이미지 다운로드
        - ResNet50 특징 추출
        - L2 normalization
        Returns: numpy array (2048,)
        """
        
    def batch_extract_features(images, batch_size=32):
        """배치 처리로 여러 이미지 벡터화"""
        
    def compute_similarity(emb1, emb2):
        """코사인 유사도 계산 (0-1 범위)"""
```

#### 특징
- **모델**: ResNet50 (fc layer 제거)
- **출력**: 2048차원 float32 벡터
- **정규화**: L2 normalization (norm = 1.0)
- **캐싱**: Django cache (1시간)
- **배치**: batch_size=32

### 2. FaissIndexManager
**파일**: `apps/recommendations/services/faiss_manager.py`

#### 주요 메서드
```python
class FaissIndexManager:
    def __init__(self, dimension=2048):
        """IndexFlatL2 초기화"""
        
    def add_vectors(vectors, product_ids):
        """벡터 추가 (product_id 매핑 유지)"""
        
    def search(query_vector, k=10, exclude_product_id=None):
        """
        K-NN 검색
        Returns: [
            {
                'product_id': str,
                'distance': float,
                'similarity': float  # 1 / (1 + distance)
            }
        ]
        """
        
    def remove_by_product_id(product_id):
        """특정 상품 벡터 제거 (인덱스 재구축)"""
        
    def save() / load():
        """인덱스 저장/로드 (data/faiss/)"""
```

#### 특징
- **인덱스**: IndexFlatL2 (정확한 L2 distance)
- **차원**: 2048
- **매핑**: product_id ↔ index 매핑
- **저장**: faiss 파일 + pickle 매핑
- **유사도**: 1 / (1 + L2_distance)

### 3. ImageEmbedding Model
**파일**: `apps/recommendations/models.py`

```python
class ImageEmbedding(models.Model):
    product_id = CharField(max_length=100, unique=True, db_index=True)
    image_url = URLField(max_length=2000)
    embedding_vector = JSONField()  # 2048-length array
    model_version = CharField(max_length=50, default='resnet50')
    created_at = DateTimeField(auto_now_add=True, db_index=True)
    updated_at = DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'image_embeddings'
        indexes = [
            Index(fields=['product_id', 'created_at']),
            Index(fields=['model_version', '-created_at']),
        ]
```

## API 엔드포인트

### 1. 유사 이미지 검색
```http
GET /api/recommendations/similar-images/{product_id}/
```

**쿼리 파라미터**:
- `limit` (int): 결과 개수 (기본: 10, 최대: 50)
- `category` (str): 카테고리 필터 (slug)
- `min_similarity` (float): 최소 유사도 (0-1, 기본: 0.5)
- `rebuild` (bool): 임베딩 재생성 (기본: false)

**응답 예시**:
```json
{
  "product_id": "P001",
  "source_product": {
    "name": "네이비 다운 재킷",
    "image_url": "https://...",
    "category": "다운",
    "brand": "노스페이스"
  },
  "similar_products": [
    {
      "product_id": "P002",
      "name": "블랙 다운 파카",
      "brand": "파타고니아",
      "category": "다운",
      "category_slug": "down",
      "image_url": "https://...",
      "price": 250000,
      "discount_rate": 20,
      "final_price": 200000,
      "similarity_score": 0.8524,
      "distance": 0.1732
    }
  ],
  "total_count": 8,
  "search_params": {
    "limit": 10,
    "category": "down",
    "min_similarity": 0.5
  }
}
```

### 2. 인덱스 통계
```http
GET /api/recommendations/image-index-stats/
```

**응답 예시**:
```json
{
  "faiss_index": {
    "total_vectors": 1523,
    "dimension": 2048,
    "product_count": 1523,
    "index_file_exists": true,
    "mapping_file_exists": true
  },
  "database": {
    "total_embeddings": 1523,
    "products_with_images": 2045,
    "coverage_rate": 74.48
  },
  "status": "healthy"
}
```

## Management Command

### generate_embeddings
전체 상품 이미지 임베딩 생성 및 Faiss 인덱스 구축

```bash
# 기본 실행
python manage.py generate_embeddings

# 옵션
python manage.py generate_embeddings --batch-size 16  # 배치 크기
python manage.py generate_embeddings --rebuild         # 전체 재생성
python manage.py generate_embeddings --category down   # 특정 카테고리만
python manage.py generate_embeddings --limit 100       # 개수 제한
python manage.py generate_embeddings --model-version resnet50
```

**실행 프로세스**:
1. 이미지가 있는 재고 상품 조회
2. 배치 단위로 임베딩 생성
3. ImageEmbedding 모델에 저장
4. Faiss 인덱스 빌드
5. 인덱스 파일 저장

**출력 예시**:
```
=== Image Embedding Generation ===
Batch size: 32
Model version: resnet50
Rebuild mode: False
Total products to process: 150

Processing batch 1/5 (32 products)
  [1/150] Processing P001... ✓
  [2/150] Processing P002... ✓
  ...
  Batch complete: 30 success, 2 failed, 0 skipped (93.8% success rate)

...

=== Building Faiss Index ===
Indexing 145 embeddings...
✓ Index built and saved

=== Generation Complete ===
Total processed: 150
Successful: 145
Failed: 5
Elapsed time: 98.3s
Average time per product: 0.66s

Faiss index stats:
  Total vectors: 145
  Dimension: 2048
  Product count: 145
```

## 프론트엔드 통합

### 1. 위젯 사용법

#### HTML (Django Template)
```django
{% load static %}
<!DOCTYPE html>
<html>
<head>
    <link rel="stylesheet" href="{% static 'css/similar_images.css' %}">
</head>
<body>
    <!-- 메타 태그 (자동 초기화용) -->
    <meta name="product-id" content="{{ product.id }}">
    
    <!-- 위젯 컨테이너 -->
    <div id="similar-images-container" 
         data-category="{{ product.category.slug }}"
         data-limit="10">
    </div>
    
    <script src="{% static 'js/similar_images.js' %}"></script>
</body>
</html>
```

#### 재사용 가능한 위젯
```django
{% include 'recommendations/similar_images_widget.html' with product_id=product.id category=product.category.slug limit=10 %}
```

### 2. JavaScript API

```javascript
// 수동 초기화
const widget = new SimilarImagesWidget({
    productId: 'P001',
    containerId: 'similar-images-container',
    category: 'down',  // optional
    limit: 10,         // optional
    minSimilarity: 0.5 // optional
});

widget.init();
```

### 3. 스타일 커스터마이징

```css
/* 그리드 레이아웃 조정 */
.similar-images-grid {
    grid-template-columns: repeat(5, 1fr);
    gap: 15px;
}

/* 유사도 배지 색상 */
.similarity-badge.high {
    background: rgba(76, 175, 80, 0.9);  /* 80%+ */
}
.similarity-badge.medium {
    background: rgba(255, 152, 0, 0.9);  /* 60-80% */
}
.similarity-badge.low {
    background: rgba(158, 158, 158, 0.9); /* <60% */
}
```

## 테스트

### 테스트 파일
**파일**: `tests/test_image_similarity.py`

### 테스트 커버리지
```
test_image_similarity.py
├── ImageEmbeddingServiceTestCase (4 tests)
│   ├── test_preprocess_image         ✓
│   ├── test_extract_features         ✓
│   ├── test_batch_extract_features   ✓
│   └── test_compute_similarity       ✓
├── FaissIndexManagerTestCase (5 tests)
│   ├── test_add_vectors              ✓
│   ├── test_search                   ✓
│   ├── test_search_with_exclusion    ✓
│   ├── test_remove_by_product_id     ✓
│   └── test_save_and_load            ✓
├── ImageEmbeddingModelTestCase (2 tests)
│   ├── test_create_embedding         ✓
│   └── test_update_embedding         ✓
└── API Tests (5 tests, skipped)

Total: 11/11 passed (5 skipped)
Time: 0.417s
```

### 테스트 실행
```bash
# 전체 테스트
python manage.py test tests.test_image_similarity

# 특정 테스트 클래스
python manage.py test tests.test_image_similarity.FaissIndexManagerTestCase

# 특정 테스트 메서드
python manage.py test tests.test_image_similarity.ImageEmbeddingServiceTestCase.test_extract_features
```

## 성능 특성

### 임베딩 생성 성능
- **단일 이미지**: ~0.5-1.0초 (CPU)
- **배치 처리**: ~0.3-0.5초/이미지 (batch_size=32)
- **GPU 사용 시**: ~0.1초/이미지 예상

### 검색 성능
- **IndexFlatL2**: O(n) - 선형 검색
- **1,000개 벡터**: <10ms
- **10,000개 벡터**: ~50ms
- **100,000개 벡터**: ~500ms

### 최적화 옵션
1. **GPU 가속** (PyTorch CUDA)
2. **IVF 인덱스** (Faiss IVFFlat/IVFPQ)
3. **양자화** (Product Quantization)
4. **샤딩** (다중 인덱스)

### 메모리 사용량
- **ResNet50 모델**: ~100MB
- **임베딩 1개**: 8KB (2048 × float32)
- **10,000 임베딩**: ~80MB
- **Faiss 인덱스**: 임베딩과 동일

## 배포 고려사항

### 1. 초기 인덱스 빌드
```bash
# 프로덕션 배포 전
python manage.py generate_embeddings --batch-size 64
```

### 2. 정기 업데이트
```bash
# Cron 또는 Celery Beat
0 2 * * * cd /app && python manage.py generate_embeddings --batch-size 32
```

### 3. 환경 변수
```python
# settings.py
FAISS_INDEX_DIR = os.path.join(BASE_DIR, 'data', 'faiss')
IMAGE_EMBEDDING_CACHE_TIMEOUT = 3600  # 1 hour
EMBEDDING_BATCH_SIZE = 32
```

### 4. Docker 설정
```dockerfile
# Dockerfile
RUN pip install torch torchvision faiss-cpu

# GPU 버전
RUN pip install torch torchvision faiss-gpu
```

### 5. 스토리지
- Faiss 인덱스: 영구 볼륨 마운트
- 모델 가중치: Docker 이미지에 포함 또는 S3

## 트러블슈팅

### 1. "CUDA not available"
**원인**: GPU 없음 또는 CUDA 미설치  
**해결**: CPU 모드로 실행 (기본 설정)

### 2. "Memory error during batch processing"
**원인**: 배치 크기 너무 큼  
**해결**: `--batch-size` 줄이기 (16 또는 8)

### 3. "Faiss index not found"
**원인**: 인덱스 파일 없음  
**해결**: `generate_embeddings` 커맨드 실행

### 4. "Slow search performance"
**원인**: IndexFlatL2는 O(n)  
**해결**: IVFFlat 인덱스로 전환

### 5. "Out of memory"
**원인**: 너무 많은 벡터  
**해결**: 
- Product Quantization 사용
- 인덱스 샤딩
- GPU 메모리 확장

## 향후 개선사항

### 1. 성능 최적화
- [ ] GPU 지원 (CUDA)
- [ ] IVF 인덱스 (빠른 검색)
- [ ] Product Quantization (메모리 절감)
- [ ] 분산 인덱스 (샤딩)

### 2. 기능 확장
- [ ] 다중 이미지 지원
- [ ] 색상 기반 필터링
- [ ] 스타일 태그 자동 추출
- [ ] A/B 테스트 프레임워크

### 3. 모델 개선
- [ ] EfficientNet (더 빠름)
- [ ] Vision Transformer (더 정확함)
- [ ] Fine-tuning (패션 도메인)
- [ ] 앙상블 모델

## 참고 자료
- **ResNet50**: [Deep Residual Learning for Image Recognition](https://arxiv.org/abs/1512.03385)
- **Faiss**: [Facebook AI Similarity Search](https://github.com/facebookresearch/faiss)
- **PyTorch**: [torchvision.models](https://pytorch.org/vision/stable/models.html)

## 작성자
- **날짜**: 2024-11-24
- **버전**: 1.0.0
- **Phase**: P2-2 (Image Similarity)
