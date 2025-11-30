# E-wall Django Project

**아웃도어 이월 상품 검색 플랫폼** - Django DRF 기반 제휴 마케팅 서비스

## 프로젝트 개요

E-wall은 아웃도어/고품질 브랜드의 이월 상품을 한 곳에서 비교하고 검색할 수 있는 제휴 마케팅 플랫폼입니다.

### 주요 기능

- 🔍 **브랜드×카테고리 검색**: 전문 속성 필터로 상세 검색
- 💰 **가격 비교**: 여러 제휴사 가격 실시간 비교
- 🔔 **가격 알림**: 조건 충족 시 자동 이메일 알림
- 🤖 **AI 카테고리 분류**: ResNet50 이미지 임베딩 기반 자동 분류 (80% 정확도)
- 🎯 **유사 상품 추천**: FAISS 벡터 검색으로 스타일 기반 추천
- 📊 **SEO 최적화**: 자동 랜딩 페이지 및 사이트맵 생성
- 📈 **클릭 트래킹**: 상세한 분석 및 집계
- 🔍 **Swagger API 문서**: 대화형 API 문서 및 테스트

## 기술 스택

- **Backend**: Django 5.0, Django REST Framework 3.14
- **Database**: PostgreSQL 15 / SQLite (개발)
- **Cache**: Redis 7
- **Task Queue**: Celery 5.3
- **AI/ML**: PyTorch (ResNet50), FAISS, NumPy
- **API Documentation**: drf-spectacular (Swagger/OpenAPI 3.0)
- **Deployment**: Docker, Nginx, Gunicorn

## 프로젝트 구조

```
ewall-django/
├── apps/
│   ├── core/           # 브랜드, 카테고리 모델
│   ├── products/       # 상품 모델, 네이버/쿠팡 API 크롤러
│   ├── alerts/         # 가격 알림 시스템
│   └── analytics/      # 클릭 추적
├── config/
│   └── settings/       # 환경별 설정 (development, production, testing)
├── docs/               # 📚 프로젝트 문서
│   ├── setup/          # 설치 및 시작 가이드
│   ├── api-integration/ # 네이버/쿠팡 API 통합 가이드
│   └── deployment/     # 클라우드 배포 가이드
├── scripts/            # 데이터 수집 스크립트
├── templates/          # Django 템플릿
├── tests/              # pytest 테스트
└── requirements/       # Python 의존성
```

## 빠른 시작

### 📚 문서 가이드

- **[설치 가이드](docs/setup/INSTALLATION_GUIDE.md)** - 전체 설치 과정
- **[빠른 시작](docs/setup/QUICKSTART.md)** - 5분 안에 시작하기
- **[실제 데이터 수집](docs/setup/QUICK_START_REAL_DATA.md)** - 네이버 API로 이월상품 수집
- **[네이버 API 설정](docs/api-integration/NAVER_API_SETUP.md)** - API 키 발급부터 설정까지
- **[쿠팡 파트너스 가이드](docs/api-integration/COUPANG_PARTNERS_GUIDE.md)** - 제휴 신청 방법
- **[클라우드 배포](docs/deployment/CLOUD_MIGRATION.md)** - DigitalOcean/AWS 배포

### 🚀 간편 실행 (권장)

프로젝트 루트에서 스크립트로 서버를 빠르게 시작할 수 있습니다:

**Windows (PowerShell):**
```powershell
# 초기 설정 (최초 1회)
.\setup.ps1

# 서버 시작
python manage.py runserver
```

**Docker Compose (추천):**
```bash
# 전체 스택 실행 (Django + PostgreSQL + Redis + Celery)
docker-compose up -d

# 로그 확인
docker-compose logs -f web
```

### 1. 환경 설정

```powershell
# 저장소 클론
git clone https://github.com/yourusername/ewall-django.git
cd ewall-django

# 초기 설정 스크립트 실행 (가상환경, 의존성, .env 파일 자동 생성)
.\setup.ps1
```

### 2. 네이버 API 설정 (실제 상품 데이터 수집)

1. [네이버 개발자 센터](https://developers.naver.com/apps/#/register)에서 애플리케이션 등록
2. 쇼핑 검색 API 추가
3. `.env.development` 파일에 API 키 입력:
   ```env
   NAVER_CLIENT_ID=your_client_id
   NAVER_CLIENT_SECRET=your_client_secret
   ```
4. 이월상품 수집:
   ```powershell
   python scripts\advanced_naver_outlet_loader.py
   ```

자세한 내용은 [네이버 API 설정 가이드](docs/api-integration/NAVER_API_SETUP.md)를 참고하세요.

### 2. 데이터베이스 설정

```powershell
# PostgreSQL & Redis 실행 (Docker)
docker-compose up -d db redis

# 또는 개별 실행
docker run -d --name ewall-db -e POSTGRES_DB=ewall -e POSTGRES_USER=ewall -e POSTGRES_PASSWORD=password -p 5432:5432 postgres:15
docker run -d --name ewall-redis -p 6379:6379 redis:7

# 마이그레이션
python manage.py migrate

# 슈퍼유저 생성
python manage.py createsuperuser
```

### 3. 개발 서버 실행

```powershell
# Django 개발 서버
python manage.py runserver

# Celery Worker (새 터미널)
celery -A config worker -l info

# Celery Beat (새 터미널)
celery -A config beat -l info
```

서버 실행 후 다음 URL에서 확인:
- 🌐 **메인**: http://localhost:8000/
- 🔧 **관리자**: http://localhost:8000/admin/
- 📡 **API**: http://localhost:8000/api/
- 📚 **Swagger**: http://localhost:8000/api/schema/swagger-ui/
- 📖 **ReDoc**: http://localhost:8000/api/schema/redoc/

## API 엔드포인트

### 상품 목록

```http
GET /api/products/{brand_slug}/{category_slug}/
```

**Query Parameters:**
- `downRatio`: 다운비율 (90-10, 80-20)
- `fillPowerMin`: 최소 필파워
- `priceMax`: 최대 가격
- `discountMin`: 최소 할인율
- `sort`: 정렬 (discount, price-low, price-high, newest)

### 알림 생성

```http
POST /api/alerts/
Content-Type: application/json

{
  "email": "user@example.com",
  "brand_slug": "branda",
  "category_slug": "down",
  "conditions": {
    "priceBelow": 100000,
    "discountAtLeast": 30,
    "downRatio": "90-10"
  }
}
```

### 클릭 트래킹

```http
GET /api/out/?productId={id}&subId={tracking_id}
```

## 관리자 페이지

http://localhost:8000/admin/ 에서 다음을 관리할 수 있습니다:

- 브랜드 및 카테고리
- 상품 (7개 카테고리별)
- 알림 설정
- 이메일 큐
- 클릭 통계

## 테스트

```powershell
# 전체 테스트 실행
pytest

# 커버리지 포함
pytest --cov=apps --cov-report=html

# 특정 테스트만 실행
pytest tests/products/test_models.py
```

## Celery 태스크

### 주기적 태스크

- **sync_naver_outlet_products**: 4시간마다 네이버 이월상품 크롤링
- **update_product_prices**: 4시간마다 가격 업데이트
- **check_price_alerts**: 1시간마다 가격 알림 체크
- **send_queued_emails**: 5분마다 이메일 발송
- **snapshot_prices**: 매일 자정 가격 스냅샷 저장
- **aggregate_daily_clicks**: 매일 오전 2시 클릭 집계

### 수동 실행

```powershell
# Django shell에서
python manage.py shell

>>> from apps.products.tasks import sync_naver_outlet_products
>>> sync_naver_outlet_products.delay()
```

## 실제 데이터 수집

### 네이버 쇼핑 API

```powershell
# 고급 이월상품 로더 (품질 필터링 포함)
python scripts\advanced_naver_outlet_loader.py

# 간단한 수집 (테스트용)
python scripts\collect_naver_outlet_products.py

# 가격 업데이트
python scripts\update_product_prices.py
```

**수집 전략:**
- 브랜드 x 키워드 조합 검색 (노스페이스 이월, 파타고니아 아울렛 등)
- 할인율 30% 이상 필터링
- 프리미엄 브랜드만 선별
- 중복 제거 (productId 기반)
- 자동 카테고리/브랜드 매핑

자세한 내용은 [상품 데이터 가이드](docs/api-integration/PRODUCT_DATA_GUIDE.md)를 참고하세요.

## 배포

### 환경별 설정

E-wall은 환경별로 설정이 분리되어 있습니다:

- `config/settings/development.py` - 로컬 개발 (SQLite, LocMemCache)
- `config/settings/production.py` - 프로덕션 (PostgreSQL, Redis, HTTPS)
- `config/settings/testing.py` - 테스트 환경

환경변수 `DJANGO_ENV`로 설정 전환:
```bash
export DJANGO_ENV=production  # Linux/Mac
$env:DJANGO_ENV="production"  # Windows PowerShell
```

### Production 설정

```powershell
# Production 의존성 설치
pip install -r requirements\production.txt

# 환경변수 설정 (.env.production)
SECRET_KEY=your-secure-random-key
DEBUG=False
ALLOWED_HOSTS=yourdomain.com
DATABASE_URL=postgresql://user:pass@localhost/ewall
REDIS_URL=redis://localhost:6379/0

# 정적 파일 수집
python manage.py collectstatic --noinput

# Gunicorn 실행
gunicorn config.wsgi:application --bind 0.0.0.0:8000 --workers 4
```

### 클라우드 배포

**DigitalOcean App Platform** (가장 간단, $12/월):
```bash
# GitHub 연동 후 자동 배포
# 자세한 내용: docs/deployment/CLOUD_MIGRATION.md
```

**AWS Lightsail** ($5-10/월):
```bash
# 자세한 내용: docs/deployment/CLOUD_MIGRATION.md
```

**Docker Production**:
```bash
# 프로덕션 이미지 빌드
docker build -t ewall:prod .

# 실행
docker-compose -f docker-compose.yml up -d
```

자세한 배포 가이드는 [클라우드 마이그레이션 문서](docs/deployment/CLOUD_MIGRATION.md)를 참고하세요.

## 환경변수

주요 환경변수는 `.env.example` 파일을 참고하세요.

```env
# Django
SECRET_KEY=your-secret-key
DEBUG=False
DJANGO_ENV=production
ALLOWED_HOSTS=yourdomain.com

# Database
DATABASE_URL=postgresql://user:pass@localhost/ewall

# Cache
REDIS_URL=redis://localhost:6379/0

# 네이버 쇼핑 API
NAVER_CLIENT_ID=your_client_id
NAVER_CLIENT_SECRET=your_client_secret

# 쿠팡 파트너스 API
COUPANG_ACCESS_KEY=your-key
COUPANG_SECRET_KEY=your-secret
COUPANG_SUBID=ewall-tracking

# Email (선택)
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
```

## 주요 문서

### 🚀 시작하기
- [설치 가이드](docs/setup/INSTALLATION_GUIDE.md)
- [빠른 시작](docs/setup/QUICKSTART.md)
- [실제 데이터 시작](docs/setup/QUICK_START_REAL_DATA.md)
- [다음 단계](docs/setup/NEXT_STEPS_NAVER.md)

### 🔌 API 통합
- [네이버 API 설정](docs/api-integration/NAVER_API_SETUP.md)
- [네이버 API 필드](docs/api-integration/NAVER_API_FIELDS.md)
- [쿠팡 파트너스 가이드](docs/api-integration/COUPANG_PARTNERS_GUIDE.md)
- [상품 데이터 가이드](docs/api-integration/PRODUCT_DATA_GUIDE.md)

### 🚢 배포
- [클라우드 마이그레이션](docs/deployment/CLOUD_MIGRATION.md)
- [Django 마이그레이션](docs/deployment/DJANGO_MIGRATION_GUIDE.md)

### 🤖 AI 기능
- [AI 상태 보고서](docs/AI_STATUS_REPORT.md)
- [추천 시스템](docs/P2-1_RECOMMENDATION_SYSTEM.md)
- [이미지 유사도](docs/P2-2_IMAGE_SIMILARITY.md)
- [텍스처 생성기](docs/TEXTURE_GENERATOR_UPGRADE.md)

## 기여하기

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## 라이선스

This project is licensed under the MIT License.

## 문의

프로젝트 관련 문의사항은 GitHub Issues를 이용해주세요.

---

**E-wall** - 아웃도어 이월 특가를 쉽고 빠르게 🏔️
