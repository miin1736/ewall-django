# E-wall 기술 스택

**E-wall 플랫폼의 전체 기술 스택 및 의존성**

## 📋 목차

1. [핵심 기술 스택](#핵심-기술-스택)
2. [백엔드 프레임워크](#백엔드-프레임워크)
3. [데이터베이스 & 캐시](#데이터베이스--캐시)
4. [AI/ML 스택](#aiml-스택)
5. [비동기 작업](#비동기-작업)
6. [프론트엔드](#프론트엔드)
7. [배포 & 인프라](#배포--인프라)
8. [개발 도구](#개발-도구)
9. [의존성 관리](#의존성-관리)

---

## 핵심 기술 스택

### 기술 스택 개요

| 분류 | 기술 | 버전 | 용도 |
|------|------|------|------|
| **Language** | Python | 3.10+ | 메인 개발 언어 |
| **Framework** | Django | 5.0 | 웹 프레임워크 |
| **API** | Django REST Framework | 3.14 | RESTful API |
| **Database** | PostgreSQL | 15 | 프로덕션 DB |
| **Database** | SQLite | 3 | 개발 DB |
| **Cache** | Redis | 7 | 캐시 & 세션 |
| **Task Queue** | Celery | 5.3 | 비동기 작업 |
| **ML Framework** | PyTorch | 2.9.1 | 딥러닝 |
| **Vector DB** | FAISS | 1.13.0 | 벡터 검색 |
| **Web Server** | Nginx | 1.25 | 리버스 프록시 |
| **WSGI Server** | Gunicorn | 21.2 | Python WSGI |
| **Container** | Docker | 24+ | 컨테이너화 |

---

## 백엔드 프레임워크

### 1. Django 5.0

**선택 이유:**
- ✅ 풍부한 ORM 및 Admin 기능
- ✅ 보안 기능 내장 (CSRF, XSS, SQL Injection 방지)
- ✅ 확장 가능한 앱 구조
- ✅ 대규모 커뮤니티 및 생태계

**주요 설정:**

```python
# config/settings/base.py
INSTALLED_APPS = [
    # Django Apps
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party Apps
    'rest_framework',
    'django_filters',
    'corsheaders',
    'drf_spectacular',
    
    # Local Apps
    'apps.core',
    'apps.products',
    'apps.recommendations',
    'apps.alerts',
    'apps.analytics',
    'apps.frontend',
]
```

### 2. Django REST Framework 3.14

**기능:**
- RESTful API 엔드포인트
- 자동 API 브라우징
- 직렬화 (Serialization)
- 인증 & 권한 (향후)

**설정:**

```python
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
    'DEFAULT_SCHEMA_CLASS': 'drf_spectacular.openapi.AutoSchema',
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
}
```

### 3. drf-spectacular (Swagger/OpenAPI)

**버전:** 0.27+

**기능:**
- OpenAPI 3.0 스키마 자동 생성
- Swagger UI 제공
- ReDoc UI 제공
- API 문서 자동화

**엔드포인트:**
- `/api/schema/swagger-ui/` - Swagger UI
- `/api/schema/redoc/` - ReDoc UI
- `/api/schema/` - OpenAPI JSON

---

## 데이터베이스 & 캐시

### 1. PostgreSQL 15 (프로덕션)

**특징:**
- 강력한 ACID 보장
- JSON 필드 지원 (임베딩 벡터 저장)
- 고급 인덱싱
- 확장성

**연결 설정:**

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('DB_NAME', 'ewall'),
        'USER': os.getenv('DB_USER', 'ewall'),
        'PASSWORD': os.getenv('DB_PASSWORD'),
        'HOST': os.getenv('DB_HOST', 'localhost'),
        'PORT': os.getenv('DB_PORT', '5432'),
    }
}
```

### 2. SQLite 3 (개발)

**사용 이유:**
- 설정 불필요
- 빠른 개발 시작
- 파일 기반 DB

**설정:**

```python
# config/settings/development.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

### 3. Redis 7 (캐시 & 세션)

**용도:**
- Django 캐시 백엔드
- 세션 스토어
- Celery 메시지 브로커
- Celery 결과 백엔드

**설정:**

```python
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
        }
    }
}

SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

**Redis 데이터베이스 분리:**
- DB 0: Celery 브로커
- DB 1: Django 캐시 & 세션
- DB 2: Celery 결과 백엔드

---

## AI/ML 스택

### 1. PyTorch 2.9.1

**용도:**
- ResNet50 이미지 임베딩 모델
- 딥러닝 추론

**설치:**
```bash
pip install torch==2.9.1 torchvision==0.24.1
```

**주요 사용:**

```python
import torch
import torchvision.models as models
from torchvision import transforms

# ResNet50 모델 로드 (ImageNet 사전학습)
model = models.resnet50(pretrained=True)
model.eval()

# FC layer 제거 (2048-dim 임베딩)
model = torch.nn.Sequential(*list(model.children())[:-1])

# 이미지 전처리
transform = transforms.Compose([
    transforms.Resize(256),
    transforms.CenterCrop(224),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])
```

### 2. FAISS 1.13.0

**Facebook AI Similarity Search**

**용도:**
- 벡터 유사도 검색
- K-NN (K-Nearest Neighbors)
- 고속 이미지 추천

**설치:**
```bash
pip install faiss-cpu==1.13.0
```

**주요 사용:**

```python
import faiss
import numpy as np

# L2 거리 기반 인덱스
dimension = 2048
index = faiss.IndexFlatL2(dimension)

# 벡터 추가
vectors = np.array(embeddings, dtype=np.float32)
index.add(vectors)

# 유사도 검색 (K=10)
distances, indices = index.search(query_vector, k=10)
```

**현재 인덱스 크기:**
- 벡터 개수: 422개
- 차원: 2048
- 인덱스 타입: IndexFlatL2
- 파일 크기: ~3.4MB

### 3. NumPy 2.3.5

**용도:**
- 벡터 연산
- L2 정규화
- 코사인 유사도 계산

```python
import numpy as np

# L2 정규화
def normalize_vector(vec):
    norm = np.linalg.norm(vec)
    return vec / norm if norm > 0 else vec

# 코사인 유사도
def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))
```

### 4. Hugging Face Hub

**용도:**
- FLUX.1-dev 텍스처 생성 (향후)
- 모델 다운로드 및 관리

---

## 비동기 작업

### 1. Celery 5.3

**분산 태스크 큐**

**설치:**
```bash
pip install celery==5.3 redis==5.0
```

**설정:**

```python
# config/celery.py
from celery import Celery
from celery.schedules import crontab

app = Celery('ewall')
app.config_from_object('django.conf:settings', namespace='CELERY')

# 주기적 태스크 스케줄
app.conf.beat_schedule = {
    'sync-naver-products': {
        'task': 'apps.products.tasks.sync_naver_outlet_products',
        'schedule': crontab(hour='*/4'),  # 4시간마다
    },
    'check-price-alerts': {
        'task': 'apps.alerts.tasks.check_price_alerts',
        'schedule': crontab(hour='*/1'),  # 1시간마다
    },
    'send-queued-emails': {
        'task': 'apps.alerts.tasks.send_queued_emails',
        'schedule': crontab(minute='*/5'),  # 5분마다
    },
}
```

**워커 실행:**
```bash
# Windows
celery -A config worker -l info -P solo

# Linux/Mac
celery -A config worker -l info
```

**Beat 실행:**
```bash
celery -A config beat -l info
```

### 2. Redis 7 (메시지 브로커)

**Celery 브로커 설정:**

```python
CELERY_BROKER_URL = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('REDIS_URL', 'redis://localhost:6379/2')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = 'Asia/Seoul'
```

---

## 프론트엔드

### 1. Django 템플릿 엔진

**버전:** Django 5.0 내장

**템플릿 구조:**
```
templates/
├── base.html                # 기본 레이아웃
├── frontend/
│   ├── index.html          # 메인 페이지
│   ├── product_list.html   # 상품 목록
│   └── product_detail.html # 상품 상세
└── admin/                  # 관리자 커스텀
```

### 2. JavaScript (Vanilla)

**사용 라이브러리:**
- Fetch API (AJAX 요청)
- DOM 조작

**예시:**

```javascript
// 유사 상품 추천 API 호출
async function loadSimilarProducts(productId) {
    const response = await fetch(
        `/api/recommendations/similar-images/${productId}/?limit=10`
    );
    const data = await response.json();
    renderSimilarProducts(data.similar_products);
}
```

### 3. CSS Frameworks

**Tailwind CSS (CDN):**
```html
<link href="https://cdn.jsdelivr.net/npm/tailwindcss@2.2/dist/tailwind.min.css" rel="stylesheet">
```

---

## 배포 & 인프라

### 1. Docker 24+

**Dockerfile:**

```dockerfile
FROM python:3.10-slim

WORKDIR /app

# 시스템 의존성
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Python 의존성
COPY requirements/production.txt .
RUN pip install --no-cache-dir -r production.txt

COPY . .

# 정적 파일 수집
RUN python manage.py collectstatic --noinput

EXPOSE 8000

CMD ["gunicorn", "config.wsgi:application", "--bind", "0.0.0.0:8000"]
```

**Docker Compose:**

```yaml
version: '3.8'

services:
  web:
    build: .
    command: gunicorn config.wsgi:application --bind 0.0.0.0:8000
    volumes:
      - .:/app
      - static:/app/staticfiles
    environment:
      - DJANGO_ENV=production
    depends_on:
      - db
      - redis

  db:
    image: postgres:15
    environment:
      POSTGRES_DB: ewall
      POSTGRES_USER: ewall
      POSTGRES_PASSWORD: ${DB_PASSWORD}
    volumes:
      - postgres_data:/var/lib/postgresql/data

  redis:
    image: redis:7
    volumes:
      - redis_data:/data

  celery:
    build: .
    command: celery -A config worker -l info
    depends_on:
      - db
      - redis

  celery-beat:
    build: .
    command: celery -A config beat -l info
    depends_on:
      - db
      - redis

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./deploy/nginx.conf:/etc/nginx/nginx.conf
      - static:/app/staticfiles
    depends_on:
      - web

volumes:
  postgres_data:
  redis_data:
  static:
```

### 2. Gunicorn 21.2

**WSGI 서버**

**설정:**

```bash
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --worker-class sync \
    --timeout 120 \
    --access-logfile logs/gunicorn.access.log \
    --error-logfile logs/gunicorn.error.log \
    --log-level info
```

### 3. Nginx 1.25

**리버스 프록시 설정:**

```nginx
server {
    listen 80;
    server_name yourdomain.com;

    location / {
        proxy_pass http://web:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static/ {
        alias /app/staticfiles/;
    }

    location /media/ {
        alias /app/media/;
    }
}
```

### 4. WhiteNoise 6.6

**정적 파일 서빙**

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # ← 여기
    # ...
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

---

## 개발 도구

### 1. pytest 7.4+

**테스트 프레임워크**

```bash
pip install pytest pytest-django pytest-cov
```

**pytest.ini:**

```ini
[pytest]
DJANGO_SETTINGS_MODULE = config.settings.testing
python_files = tests.py test_*.py *_tests.py
```

**실행:**
```bash
pytest                              # 전체 테스트
pytest --cov=apps --cov-report=html # 커버리지 포함
pytest tests/products/              # 특정 앱만
```

### 2. Django Debug Toolbar 4.2

**개발 디버깅**

```python
INSTALLED_APPS = [
    # ...
    'debug_toolbar',  # 개발 환경만
]

MIDDLEWARE = [
    'debug_toolbar.middleware.DebugToolbarMiddleware',
    # ...
]

INTERNAL_IPS = ['127.0.0.1']
```

### 3. Black (코드 포매터)

```bash
pip install black
black .
```

### 4. Flake8 (린터)

```bash
pip install flake8
flake8 apps/
```

---

## 의존성 관리

### 의존성 파일 구조

```
requirements/
├── base.txt         # 공통 의존성
├── development.txt  # 개발 전용
├── production.txt   # 프로덕션 전용
└── testing.txt      # 테스트 전용
```

### base.txt (공통)

```pip-requirements
# Core Django
Django==5.0
djangorestframework==3.14
django-filter==23.5
django-redis==5.4

# Database
psycopg2-binary==2.9.10
dj-database-url==2.1

# Celery
celery==5.3
redis==5.0

# HTTP
requests==2.31.0

# Security
django-cors-headers==4.3

# Environment
python-dotenv==1.0

# Utilities
Pillow==10.1

# AI/ML
torch==2.9.1
torchvision==0.24.1
faiss-cpu==1.13.0
numpy==2.3.5

# WSGI
gunicorn==21.2
whitenoise==6.6

# API Documentation
drf-spectacular==0.27
```

### development.txt

```pip-requirements
-r base.txt

# Debug
django-debug-toolbar==4.2

# Testing
pytest==7.4
pytest-django==4.7
pytest-cov==4.1

# Code Quality
black==23.12
flake8==7.0
```

### production.txt

```pip-requirements
-r base.txt

# Monitoring (향후)
# sentry-sdk==1.40
```

---

## 버전 호환성

### Python 버전

- **권장:** Python 3.10+
- **최소:** Python 3.9
- **최대:** Python 3.12

### Django 버전

- **현재:** Django 5.0
- **호환:** Django 4.2 LTS

### 데이터베이스 버전

- **PostgreSQL:** 12+
- **SQLite:** 3.31+
- **Redis:** 6+

---

## 클라우드 서비스 (옵션)

### AWS 서비스

| 서비스 | 용도 | 대안 |
|--------|------|------|
| EC2 | 애플리케이션 서버 | DigitalOcean Droplet |
| RDS | PostgreSQL 관리형 | DigitalOcean Managed DB |
| ElastiCache | Redis 관리형 | DigitalOcean Managed Redis |
| S3 | 정적 파일 저장 | DigitalOcean Spaces |
| CloudFront | CDN | CloudFlare |

### DigitalOcean 서비스

- **App Platform**: $12/월 (자동 배포)
- **Managed PostgreSQL**: $15/월
- **Managed Redis**: $15/월
- **Spaces (S3 호환)**: $5/월

---

## 보안 라이브러리

```bash
# CORS
django-cors-headers==4.3

# Rate Limiting
django-ratelimit==4.1

# 환경변수
python-dotenv==1.0
```

---

## 성능 최적화

### 데이터베이스 최적화

```python
# 쿼리 최적화
products = Product.objects.select_related('brand', 'category')
products = Product.objects.prefetch_related('imageembedding_set')

# 인덱스
class Meta:
    indexes = [
        models.Index(fields=['brand', 'category']),
        models.Index(fields=['in_stock', '-created_at']),
    ]
```

### 캐싱

```python
from django.core.cache import cache

# 임베딩 캐시
cache.set(f'embedding:{product_id}', vector, timeout=3600)

# API 응답 캐시
@cache_page(60 * 15)  # 15분
def api_view(request):
    pass
```

---

## 참고 자료

### 공식 문서

- [Django 5.0 Docs](https://docs.djangoproject.com/en/5.0/)
- [DRF Docs](https://www.django-rest-framework.org/)
- [Celery Docs](https://docs.celeryproject.org/)
- [PyTorch Docs](https://pytorch.org/docs/stable/)
- [FAISS Wiki](https://github.com/facebookresearch/faiss/wiki)

### 관련 프로젝트 문서

- [API 문서](API_DOCUMENTATION.md)
- [아키텍처 문서](ARCHITECTURE.md)
- [AI 상태 보고서](AI_STATUS_REPORT.md)
