# E-wall Django Quick Start Guide

## 🚀 빠른 시작 (Windows PowerShell)

### 방법 1: 자동 설정 스크립트 사용

```powershell
# PowerShell 스크립트 실행 권한 설정 (필요시)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# 설정 스크립트 실행
.\setup.ps1
```

### 방법 2: 수동 설정

#### 1. 가상환경 생성 및 활성화

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

#### 2. 패키지 설치

```powershell
pip install -r requirements\base.txt
```

#### 3. 환경변수 설정

```powershell
Copy-Item .env.example .env
# .env 파일을 편집하여 필요한 값 설정
```

#### 4. PostgreSQL & Redis 실행 (Docker)

```powershell
# PostgreSQL
docker run -d --name ewall-db `
  -e POSTGRES_DB=ewall `
  -e POSTGRES_USER=ewall `
  -e POSTGRES_PASSWORD=password `
  -p 5432:5432 `
  postgres:15

# Redis
docker run -d --name ewall-redis -p 6379:6379 redis:7
```

#### 5. 데이터베이스 마이그레이션

```powershell
python manage.py makemigrations
python manage.py migrate
```

#### 6. 슈퍼유저 생성

```powershell
python manage.py createsuperuser
```

#### 7. 초기 데이터 생성

```powershell
python manage.py shell
```

```python
from apps.core.models import Brand, Category

# 브랜드 생성
Brand.objects.create(name='노스페이스', slug='northface')
Brand.objects.create(name='파타고니아', slug='patagonia')
Brand.objects.create(name='아크테릭스', slug='arcteryx')

# 카테고리 생성
Category.objects.create(name='다운', slug='down', category_type='down')
Category.objects.create(name='슬랙스', slug='slacks', category_type='slacks')
Category.objects.create(name='청바지', slug='jeans', category_type='jeans')
```

#### 8. 개발 서버 실행

```powershell
# 터미널 1: Django 개발 서버
python manage.py runserver

# 터미널 2: Celery Worker
celery -A config worker -l info

# 터미널 3: Celery Beat
celery -A config beat -l info
```

## 🐳 Docker Compose로 실행

```powershell
# 전체 스택 실행
docker-compose up -d

# 마이그레이션 (처음 한 번만)
docker-compose exec web python manage.py migrate

# 슈퍼유저 생성
docker-compose exec web python manage.py createsuperuser

# 로그 확인
docker-compose logs -f web
```

## 📝 주요 URL

- **홈페이지**: http://localhost:8000/
- **관리자**: http://localhost:8000/admin/
- **API 문서**: http://localhost:8000/api/
- **상품 목록 API**: http://localhost:8000/api/products/{brand}/{category}/

## 🧪 테스트 실행

```powershell
# 전체 테스트
pytest

# 커버리지 포함
pytest --cov=apps --cov-report=html

# 특정 앱만 테스트
pytest tests/products/
```

## 🔧 문제 해결

### PostgreSQL 연결 오류

```powershell
# Docker 컨테이너 확인
docker ps

# PostgreSQL 로그 확인
docker logs ewall-db

# 연결 테스트
docker exec -it ewall-db psql -U ewall -d ewall
```

### Celery 작동 확인

```powershell
# Celery 상태 확인
celery -A config status

# 태스크 테스트
celery -A config shell
```

```python
from apps.products.tasks import sync_feeds
result = sync_feeds.delay('coupang')
print(result.get())
```

### Redis 연결 확인

```powershell
# Redis CLI 접속
docker exec -it ewall-redis redis-cli

# 연결 테스트
> PING
PONG
```

## 📚 추가 자료

- [Django 공식 문서](https://docs.djangoproject.com/)
- [DRF 공식 문서](https://www.django-rest-framework.org/)
- [Celery 공식 문서](https://docs.celeryq.dev/)
- [프로젝트 마이그레이션 가이드](DJANGO_MIGRATION_GUIDE.md)

## 💡 개발 팁

### 새 앱 추가

```powershell
python manage.py startapp new_app apps/new_app
```

### 마이그레이션 생성

```powershell
python manage.py makemigrations app_name
python manage.py migrate
```

### Django Shell 사용

```powershell
python manage.py shell
```

### 정적 파일 수집 (프로덕션)

```powershell
python manage.py collectstatic
```

---

**문제가 있으신가요?** GitHub Issues에 등록해주세요!
