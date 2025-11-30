# AI 기능 설치 가이드

## 개요
이 프로젝트의 AI 기능(이미지 유사도 검색, 질감 생성)을 사용하려면 추가 패키지 설치가 필요합니다.

## 필수 패키지

### 1. 이미지 유사도 검색
- **PyTorch** (torch, torchvision): ResNet50 모델
- **Faiss**: 벡터 유사도 검색
- **NumPy**: 벡터 연산

### 2. 질감 생성
- **Hugging Face API 토큰**: Stable Diffusion 2.1 사용

## 설치 방법

### Option 1: 모든 AI 패키지 설치
```bash
pip install -r requirements/base.txt
pip install -r requirements/ai.txt
```

### Option 2: 개별 설치
```bash
# 이미지 유사도 검색용
pip install torch==2.1.0 torchvision==0.16.0
pip install faiss-cpu==1.7.4
pip install numpy==1.24.3

# 질감 생성용 (Hugging Face API 토큰 필요)
# 환경변수만 설정하면 됨
```

## 환경 변수 설정

### Hugging Face API 토큰 (질감 생성용)
1. Hugging Face 계정 생성: https://huggingface.co/join
2. API 토큰 발급: https://huggingface.co/settings/tokens
3. `.env` 파일에 추가:
```env
HUGGING_FACE_API_TOKEN=your_token_here
```

## 설치 확인

### Python 패키지 확인
```bash
pip show torch torchvision faiss-cpu numpy
```

### API 동작 확인
```bash
# 서버 실행
python manage.py runserver

# 테스트 요청
curl http://127.0.0.1:8000/api/recommendations/image-stats/
```

## 패키지 미설치 시 동작

### 이미지 유사도 검색
- **에러 응답 (503)**: 
```json
{
  "error": "AI 기능을 사용할 수 없습니다",
  "missing_packages": ["torch", "torchvision", "faiss-cpu", "numpy"],
  "install_command": "pip install torch torchvision faiss-cpu numpy"
}
```

### 질감 생성
- **에러 응답 (503)**:
```json
{
  "error": "AI 질감 생성 기능을 사용할 수 없습니다",
  "reason": "Hugging Face API 토큰이 설정되지 않았습니다",
  "solution": "환경변수 HUGGING_FACE_API_TOKEN을 설정해주세요"
}
```

## 패키지 크기

- **torch**: ~200MB
- **torchvision**: ~5MB
- **faiss-cpu**: ~10MB
- **numpy**: ~15MB
- **총합**: ~230MB

## 대안 (경량화)

### CPU 전용 PyTorch 사용 (기본값)
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cpu
```

### GPU 버전 (CUDA 11.8)
```bash
pip install torch torchvision --index-url https://download.pytorch.org/whl/cu118
```

## 트러블슈팅

### 1. torch 설치 실패
```bash
# CPU 전용 버전 명시적 설치
pip install torch==2.1.0+cpu torchvision==0.16.0+cpu -f https://download.pytorch.org/whl/torch_stable.html
```

### 2. faiss-cpu 설치 실패
```bash
# conda 사용 시
conda install faiss-cpu -c conda-forge
```

### 3. numpy 버전 충돌
```bash
pip install numpy==1.24.3 --force-reinstall
```

### 4. API 토큰 오류
- `.env` 파일이 루트 디렉터리에 있는지 확인
- 서버 재시작 후 토큰 적용 확인
- 토큰 권한 확인 (read 권한 필요)

## 개발 환경 권장 사항

### 로컬 개발
```bash
# AI 패키지 없이 개발 가능
# API는 명확한 에러 메시지 반환
pip install -r requirements/base.txt
```

### 프로덕션 배포
```bash
# AI 기능 필수 설치
pip install -r requirements/base.txt
pip install -r requirements/ai.txt
```

## 참고 문서
- PyTorch 설치: https://pytorch.org/get-started/locally/
- Faiss 가이드: https://github.com/facebookresearch/faiss
- Hugging Face API: https://huggingface.co/docs/api-inference/
