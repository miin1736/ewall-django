# E-wall 프로젝트 문서

E-wall Django 프로젝트의 전체 문서 모음입니다.

## 📁 문서 구조

### 🚀 Setup - 설치 및 시작 가이드

프로젝트를 처음 시작하는 분들을 위한 가이드입니다.

| 문서 | 설명 | 소요 시간 |
|------|------|----------|
| [INSTALLATION_GUIDE.md](setup/INSTALLATION_GUIDE.md) | 전체 설치 프로세스 상세 가이드 | 30분 |
| [QUICKSTART.md](setup/QUICKSTART.md) | 5분 안에 빠르게 시작하기 | 5분 |
| [QUICK_START_REAL_DATA.md](setup/QUICK_START_REAL_DATA.md) | 실제 이월상품 데이터 수집 시작 | 10분 |
| [NEXT_STEPS_NAVER.md](setup/NEXT_STEPS_NAVER.md) | 네이버 API 설정 후 다음 단계 | 20분 |

**추천 순서:**
1. QUICKSTART.md (개발 환경 구축)
2. QUICK_START_REAL_DATA.md (네이버 API 설정 및 데이터 수집)
3. NEXT_STEPS_NAVER.md (홈페이지 표시 및 자동화)

---

### 🔌 API Integration - API 통합 가이드

네이버 쇼핑 API와 쿠팡 파트너스 API 통합 관련 문서입니다.

| 문서 | 설명 | 비고 |
|------|------|------|
| [NAVER_API_SETUP.md](api-integration/NAVER_API_SETUP.md) | 네이버 API 키 발급 및 설정 | 무료, 즉시 사용 |
| [NAVER_API_FIELDS.md](api-integration/NAVER_API_FIELDS.md) | 네이버 API 응답 필드 상세 설명 | 14개 필드 |
| [PRODUCT_DATA_GUIDE.md](api-integration/PRODUCT_DATA_GUIDE.md) | 실제 상품 데이터 수집 완벽 가이드 | 종합 가이드 |
| [COUPANG_PARTNERS_GUIDE.md](api-integration/COUPANG_PARTNERS_GUIDE.md) | 쿠팡 파트너스 신청 방법 | 승인 1-3일 소요 |

**네이버 API 활용:**
- 무료 일 25,000건 검색 가능
- 가격, 이미지, 브랜드, 할인율 정보 제공
- 실시간 가격 업데이트 가능
- 구매 링크로 실제 쇼핑몰 연결

**쿠팡 API 활용:**
- 수수료 1.5~9% 수익 창출
- 딥링크로 클릭 추적
- 승인 후 즉시 사용

---

### 🚢 Deployment - 배포 가이드

프로덕션 환경 배포 및 클라우드 마이그레이션 가이드입니다.

| 문서 | 설명 | 비용 |
|------|------|------|
| [CLOUD_MIGRATION.md](deployment/CLOUD_MIGRATION.md) | DigitalOcean, AWS 등 클라우드 배포 | $5-24/월 |
| [DJANGO_MIGRATION_GUIDE.md](deployment/DJANGO_MIGRATION_GUIDE.md) | Django 프로덕션 환경 마이그레이션 | - |

**배포 옵션:**
1. **DigitalOcean App Platform** (추천): $12/월, GitHub 연동 자동 배포
2. **AWS Lightsail**: $5-10/월, 수동 설정 필요
3. **DigitalOcean Droplet**: $6/월, Docker 직접 관리

**환경 구성:**
- Development: SQLite + LocMemCache (로컬 개발)
- Production: PostgreSQL + Redis + Gunicorn + Nginx
- Testing: SQLite + LocMemCache (테스트)

---

### 🤖 AI Features - AI 기능 문서

추천 시스템, 이미지 유사도, 텍스처 생성 등 AI 기능 관련 문서입니다.

| 문서 | 설명 | 상태 |
|------|------|------|
| [AI_STATUS_REPORT.md](AI_STATUS_REPORT.md) | AI 기능 전체 상태 보고서 | ✅ 활성 |
| [P2-1_RECOMMENDATION_SYSTEM.md](P2-1_RECOMMENDATION_SYSTEM.md) | 협업 필터링 기반 추천 시스템 | ✅ 구현 |
| [P2-1_TEST_RESULTS.md](P2-1_TEST_RESULTS.md) | 추천 시스템 테스트 결과 | ✅ 검증 |
| [P2-2_IMAGE_SIMILARITY.md](P2-2_IMAGE_SIMILARITY.md) | FAISS 기반 이미지 유사도 검색 | ✅ 구현 |
| [TEXTURE_GENERATOR_UPGRADE.md](TEXTURE_GENERATOR_UPGRADE.md) | Hugging Face 텍스처 생성기 업그레이드 | ✅ 완료 |
| [HUGGINGFACE_MIGRATION.md](HUGGINGFACE_MIGRATION.md) | Hugging Face 모델 마이그레이션 | ✅ 완료 |

**주요 AI 기능:**
- 협업 필터링 상품 추천
- FAISS 벡터 기반 이미지 유사도 검색
- Hugging Face Transformers 텍스처 생성
- 클릭 기반 사용자 선호도 학습

---

### 📊 Advanced Features - 고급 기능 문서

SEO, 크롤러, 알림 시스템 등 고급 기능 관련 문서입니다.

| 문서 | 설명 | 우선순위 |
|------|------|----------|
| [P1-1_MULTI_PLATFORM_CRAWLER.md](P1-1_MULTI_PLATFORM_CRAWLER.md) | 멀티 플랫폼 크롤러 시스템 | 높음 |
| [P1-2_ADVANCED_ALERT_SYSTEM.md](P1-2_ADVANCED_ALERT_SYSTEM.md) | 가격 알림 시스템 고도화 | 중간 |
| [P1-3_SEO_OPTIMIZATION.md](P1-3_SEO_OPTIMIZATION.md) | SEO 최적화 및 사이트맵 | 중간 |
| [API_FILTER_DOCUMENTATION.md](API_FILTER_DOCUMENTATION.md) | API 필터 상세 문서 | 참고 |

---

## 🗂️ 문서 사용 가이드

### 새로 시작하는 경우

```
1. setup/QUICKSTART.md (5분)
   ↓
2. api-integration/NAVER_API_SETUP.md (10분)
   ↓
3. setup/QUICK_START_REAL_DATA.md (10분)
   ↓
4. setup/NEXT_STEPS_NAVER.md (20분)
```

### 프로덕션 배포하는 경우

```
1. deployment/DJANGO_MIGRATION_GUIDE.md
   ↓
2. deployment/CLOUD_MIGRATION.md
   ↓
3. 환경변수 설정 (.env.production)
   ↓
4. 배포 실행
```

### API 통합하는 경우

```
네이버 쇼핑 API (무료, 즉시):
1. api-integration/NAVER_API_SETUP.md
2. api-integration/NAVER_API_FIELDS.md
3. scripts/advanced_naver_outlet_loader.py 실행

쿠팡 파트너스 (수익화):
1. api-integration/COUPANG_PARTNERS_GUIDE.md
2. 승인 대기 (1-3일)
3. API 키 설정 및 크롤러 실행
```

---

## 📞 문의 및 기여

- 프로젝트 이슈: [GitHub Issues](https://github.com/yourusername/ewall-django/issues)
- 문서 오류: Pull Request 환영합니다
- 질문: Discussions 활용

---

**E-wall** - 아웃도어 이월 특가를 쉽고 빠르게 🏔️
