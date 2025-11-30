# AI 모델 상태 및 에러 처리 개선 완료

## 🎯 작업 완료 사항

### 1. AI 패키지 설치
✅ **모든 필수 패키지 설치 완료**
- `torch 2.9.1+cpu` - PyTorch (CPU 버전)
- `torchvision 0.24.1+cpu` - Computer Vision 모델
- `faiss-cpu 1.13.0` - 벡터 유사도 검색
- `numpy 2.3.5` - 수치 연산

### 2. 에러 처리 개선
✅ **Mock 대신 상세한 에러 메시지 반환**

#### 이미지 유사도 검색 API
**요청**: `GET /api/recommendations/similar-images/<product_id>/`

**AI 패키지 없을 때 응답 (503)**:
```json
{
  "error": "AI 기능을 사용할 수 없습니다",
  "reason": "필수 Python 패키지가 설치되지 않았습니다",
  "missing_packages": ["torch", "faiss-cpu", "numpy"],
  "install_command": "pip install torch faiss-cpu numpy",
  "details": {
    "image_embedding_available": false,
    "faiss_available": false,
    "missing_for_embedding": ["torch", "torchvision"],
    "missing_for_faiss": ["faiss-cpu", "numpy"]
  }
}
```

#### 질감 생성 API
**요청**: `POST /api/recommendations/texture/generate/`

**Hugging Face 토큰 없을 때 응답 (503)**:
```json
{
  "error": "AI 질감 생성 기능을 사용할 수 없습니다",
  "reason": "Hugging Face API 토큰이 설정되지 않았습니다",
  "details": {
    "api_token_set": false,
    "mode": "mock",
    "solution": "환경변수 HUGGING_FACE_API_TOKEN을 설정해주세요"
  },
  "instructions": {
    "1": "Hugging Face 계정 생성: https://huggingface.co/join",
    "2": "API 토큰 발급: https://huggingface.co/settings/tokens",
    "3": ".env 파일에 HUGGING_FACE_API_TOKEN=your_token_here 추가",
    "4": "서버 재시작"
  }
}
```

### 3. 코드 개선 사항

#### `image_embedding.py`
```python
# AI 패키지 가용성 체크
AI_AVAILABLE = True | False
MISSING_PACKAGES = []  # 누락된 패키지 목록

# 모든 메서드에서 패키지 체크
def extract_features(self, image):
    if not AI_AVAILABLE or self.model is None:
        logger.error(f"Cannot extract features: Missing {MISSING_PACKAGES}")
        return None
```

#### `faiss_manager.py`
```python
# Faiss 가용성 체크
FAISS_AVAILABLE = True | False
MISSING_PACKAGES = []

# 인덱스 초기화 시 체크
def __init__(self, dimension=2048):
    if not FAISS_AVAILABLE:
        self.index = None
        logger.warning(f"Faiss not available. Missing: {MISSING_PACKAGES}")
```

#### `image_api.py`
```python
# API 진입점에서 패키지 체크
def get(self, request, product_id):
    from apps.recommendations.services.image_embedding import AI_AVAILABLE
    from apps.recommendations.services.faiss_manager import FAISS_AVAILABLE
    
    if not AI_AVAILABLE or not FAISS_AVAILABLE:
        return Response({
            'error': '상세 에러 메시지',
            'missing_packages': [...],
            'install_command': 'pip install ...'
        }, status=503)
```

### 4. 새로 생성된 파일

#### `requirements/ai.txt`
AI 기능용 패키지 목록
```txt
torch==2.1.0
torchvision==0.16.0
faiss-cpu==1.7.4
numpy==1.24.3
```

#### `docs/AI_INSTALLATION.md`
AI 패키지 설치 가이드
- 설치 방법 (pip, conda)
- 환경 변수 설정
- 트러블슈팅
- 패키지 크기 정보

#### `scripts/check_ai_status.py`
AI 시스템 진단 스크립트
```bash
python scripts/check_ai_status.py
```

**출력 예시**:
```
============================================================
AI 패키지 상태 확인
============================================================

[1] ImageEmbedding Service
   ✅ AI Available: True
   ✅ All packages installed
   ✅ ResNet50 model loaded successfully

[2] Faiss Index Manager
   ✅ Faiss Available: True
   ✅ All packages installed
   ✅ Faiss index initialized (ntotal: 0)

[3] Texture Generator Service
   Mode: Hugging Face API
   ✅ Hugging Face API token configured

[4] Installed Package Versions
   torch: 2.9.1+cpu
   torchvision: 0.24.1+cpu
   numpy: 2.3.5
   faiss-cpu: installed

============================================================
✅ AI 시스템 진단 완료
============================================================
```

## 📊 현재 시스템 상태

### ✅ 정상 작동 중
- **ResNet50** 모델: 이미지 특징 추출
- **Faiss** 인덱스: 벡터 유사도 검색
- **Hugging Face API**: 질감 생성 (토큰 설정됨)

### 🔧 설치 완료 패키지
| 패키지 | 버전 | 용도 |
|-------|------|------|
| torch | 2.9.1+cpu | 딥러닝 프레임워크 |
| torchvision | 0.24.1+cpu | ResNet50 모델 |
| faiss-cpu | 1.13.0 | 벡터 검색 엔진 |
| numpy | 2.3.5 | 수치 연산 |

### 📝 사용 가능한 API

#### 1. 이미지 유사도 검색
```bash
GET /api/recommendations/similar-images/<product_id>/
```

#### 2. 질감 생성
```bash
POST /api/recommendations/texture/generate/
Body: {
  "product_id": "...",
  "material": "cotton",
  "color": "navy blue"
}
```

#### 3. Faiss 통계
```bash
GET /api/recommendations/image-stats/
```

## 🚀 다음 단계

### 1. 임베딩 생성 (필수)
```bash
python manage.py generate_embeddings --batch-size 10
```
- 모든 상품 이미지를 ResNet50으로 벡터화
- Faiss 인덱스에 저장

### 2. API 테스트
```bash
# 이미지 유사도
curl http://127.0.0.1:8000/api/recommendations/similar-images/test-product-1/

# 질감 생성
curl -X POST http://127.0.0.1:8000/api/recommendations/texture/generate/ \
  -H "Content-Type: application/json" \
  -d '{"product_id":"test-product-1","material":"cotton","color":"navy"}'
```

### 3. 프론트엔드 통합
- `/static/test_ai.html`에서 테스트 가능
- 실제 상품 페이지에 위젯 통합

## 📖 참고 문서
- **설치 가이드**: `docs/AI_INSTALLATION.md`
- **AI 기능 테스트**: `docs/AI_FEATURES_TEST_GUIDE.md`
- **API 문서**: `docs/P2-2_IMAGE_SIMILARITY.md`
