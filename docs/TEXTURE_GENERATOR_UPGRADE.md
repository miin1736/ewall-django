# Texture Generator Upgrade - Hugging Face Inference Providers

## 변경 사항 요약 (2025-11-26)

### 1. AI 서비스 완전 전환
- **이전**: Hugging Face Inference API (api-inference.huggingface.co) - 2025년 11월 중단됨
- **이후**: Hugging Face Inference Providers (router.huggingface.co)
- **이유**: 기존 API 엔드포인트가 410 Gone으로 중단되어 새로운 공식 API로 마이그레이션

### 2. AI 모델 변경
- **이전**: Stable Diffusion 2.1 / Realistic Vision v6.0 (직접 API 호출)
- **이후**: FLUX.1-dev (Hugging Face Inference Providers를 통한 접근)
- **장점**: 
  - 최신 고품질 이미지 생성 모델
  - 자동 프로바이더 선택 (Nebius, Replicate, Together AI 등)
  - 무료 티어 제공
  - 더 사실적인 fabric texture 생성

### 3. 구현 방법 변경
**이전 방식** (requests 직접 사용):
```python
import requests
response = requests.post(HF_API_URL, headers=headers, json=payload)
image = Image.open(BytesIO(response.content))
```

**새로운 방식** (InferenceClient 사용):
```python
from huggingface_hub import InferenceClient
client = InferenceClient(api_key=api_token)
image = client.text_to_image(prompt=prompt, model="black-forest-labs/FLUX.1-dev")
```

## 테스트 방법

### 1. 서버 재시작 확인
```powershell
.\restart.bat
```
✅ 완료: 서버가 http://127.0.0.1:8000/ 에서 실행 중

### 2. 테스트 페이지 접속
http://127.0.0.1:8000/static/test_ai.html

### 3. 질감 생성 테스트
1. **상품 타입**: Down Jacket 선택
2. **소재**: Nylon 선택
3. **색상**: Navy Blue 입력
4. **"질감 생성" 버튼 클릭**

### 4. 예상 결과
- ⏱️ **생성 시간**: 15-30초 (첫 실행 시 모델 로딩으로 더 오래 걸릴 수 있음)
- 🖼️ **결과물**: 네이비 블루 나일론 원단의 사실적인 근접 촬영 이미지
- 📝 **프롬프트 예시**:
  ```
  extreme close-up macro photograph of navy blue water-resistant nylon, 
  quilted pattern, technical fabric outer garment material, 
  photorealistic, 8k uhd, professional textile photography, 
  studio lighting, sharp focus, highly detailed weave pattern, 
  negative prompt: blurry, low quality, people, faces, objects, 
  watermark, text, logo, pattern design, illustration, cartoon
  ```

### 5. 에러 케이스 확인
**API 토큰 없음**:
```
ValueError: Hugging Face API token is required for texture generation.
```

**API 실패**:
```
RuntimeError: Failed to generate texture via Hugging Face API. 
Please check API status and try again.
```

**모델 로딩 중 (503)**:
```
Model is loading, please retry in 20-30 seconds
```

## 기술 스택

### AI 모델
- **Realistic Vision v6.0**: SG161222/Realistic_Vision_V6.0_B1_noVAE
- **학습 데이터**: 사실적인 사진 (의류 포함)
- **특징**: 고품질 photorealistic 이미지 생성

### API
- **Hugging Face Inference API**: Serverless 추론
- **인증**: Bearer Token (환경변수 `HUGGING_FACE_API_TOKEN`)

### 의존성
- `requests`: HTTP API 호출
- `PIL (Pillow)`: 이미지 처리
- `logging`: 로그 기록

## 다음 단계

### 권장 개선사항
1. **캐싱 시스템**: 동일한 파라미터 재요청 시 캐시된 이미지 반환
2. **배치 생성**: 여러 질감을 한 번에 생성
3. **A/B 테스트**: Realistic Vision vs 다른 모델 비교
4. **프롬프트 튜닝**: 사용자 피드백 기반 프롬프트 개선

### 모니터링 포인트
- API 호출 성공률
- 평균 생성 시간
- 사용자 만족도 (생성된 이미지 품질)
- API 비용 (Hugging Face 무료 티어 제한)

## 변경 파일
- `apps/recommendations/services/texture_generator.py` (전체 수정)
- Mock mode 관련 코드 삭제 (~80줄 감소)

## 참고 자료
- [Realistic Vision v6.0 모델 페이지](https://huggingface.co/SG161222/Realistic_Vision_V6.0_B1_noVAE)
- [Hugging Face Inference API 문서](https://huggingface.co/docs/api-inference/)
