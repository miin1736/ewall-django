# E-wall Django 마이그레이션 가이드

## ✅ 완료된 작업 (2024)

### 1. 환경별 설정 파일 분리
- ✅ `config/settings/` 디렉토리 생성
- ✅ `base.py` - 공통 설정
- ✅ `development.py` - 로컬 개발 환경
- ✅ `production.py` - 프로덕션 환경
- ✅ `testing.py` - 테스트 환경
- ✅ `__init__.py` - 자동 환경 선택

### 2. 보안 강화
- ✅ SECRET_KEY 환경변수 필수화
- ✅ DEBUG=False 프로덕션 하드코딩
- ✅ HTTPS 강제 (HSTS 포함)
- ✅ CORS 엄격한 설정
- ✅ CSRF/XSS 방어 활성화

### 3. 성능 최적화
- ✅ PostgreSQL 설정 (연결 풀링)
- ✅ Redis 다층 캐시 구조
- ✅ Read Replica 지원 (`db_router.py`)
- ✅ 캐싱 미들웨어 추가
- ✅ GZip 압축 활성화
- ✅ 사이드바 데이터 캐싱

### 4. 환경변수 파일
- ✅ `.env.development` 생성
- ✅ `.env.production` 템플릿 생성
- ✅ `.gitignore` 업데이트

### 5. 유틸리티
- ✅ `config/utils.py` - 캐싱 데코레이터
- ✅ `apps/core/tasks.py` - 캐시 워밍업
- ✅ Celery Beat 스케줄 추가

---

## 📋 다음 단계

### 1. 기존 설정 백업
```powershell
# 기존 settings.py 백업
Copy-Item config\settings.py config\settings.py.backup
```

### 2. 필수 패키지 설치
```powershell
pip install python-dotenv dj-database-url django-redis psycopg2-binary gunicorn whitenoise sentry-sdk
```

### 3. 개발 환경 테스트
```powershell
# 환경변수 설정
$env:DJANGO_ENV = "development"

# 마이그레이션
python manage.py migrate

# 서버 실행
python manage.py runserver
```

### 4. 프로덕션 배포 체크리스트
- [ ] `.env.production` 실제 값 입력
- [ ] PostgreSQL 데이터베이스 생성
- [ ] Redis 서버 설치/설정
- [ ] Gunicorn 설정
- [ ] Nginx 설정
- [ ] SSL 인증서 설치
- [ ] Sentry 프로젝트 생성
- [ ] 방화벽 설정

---

## 🚀 배포 명령어

### Gunicorn 실행
```bash
gunicorn config.wsgi:application \
  --bind 0.0.0.0:8000 \
  --workers 4 \
  --worker-class sync \
  --max-requests 1000 \
  --max-requests-jitter 50 \
  --timeout 30 \
  --access-logfile logs/access.log \
  --error-logfile logs/error.log
```

### Celery Worker & Beat
```bash
celery -A config worker -l info --pool=solo
celery -A config beat -l info
```

---

## 📊 트래픽 수용력 분석

### 현재 PC 사양 (예상)
- **CPU**: 4-8 코어
- **메모리**: 8-16GB
- **저장소**: SSD

### 트래픽별 플랜

#### Plan 1: 100-500명 (현재 PC)
- SQLite → PostgreSQL
- LocMem → Redis
- Gunicorn 4 워커
- **예상 비용**: $0 (로컬 호스팅)

#### Plan 2: 500-2,000명 (클라우드 기본)
- VPS (DigitalOcean, Linode)
- 2 vCPU, 4GB RAM
- PostgreSQL + Redis
- **예상 비용**: $24/월

#### Plan 3: 2,000-10,000명 (중급)
- 4 vCPU, 8GB RAM
- PostgreSQL Read Replica
- Redis Cluster
- Nginx 캐싱
- **예상 비용**: $96/월

#### Plan 4: 10,000-20,000명 (엔터프라이즈)
- Load Balancer + 3대 서버
- 관리형 PostgreSQL
- Redis Cluster
- CDN
- **예상 비용**: $300+/월

---

## ⚠️ 주의사항

1. **환경변수 관리**
   - `.env.production`은 절대 Git에 커밋 금지
   - 실제 SECRET_KEY 생성: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`

2. **데이터베이스 마이그레이션**
   - SQLite → PostgreSQL 전환 시 데이터 백업 필수
   - `python manage.py dumpdata > backup.json`
   - `python manage.py loaddata backup.json`

3. **Redis 연결**
   - Windows에서 Redis는 WSL2 또는 Docker 필요

4. **정적 파일 수집**
   - 배포 전 `python manage.py collectstatic` 실행

---

## 🔍 트러블슈팅

### settings.py import 에러
```python
# 기존 코드에서 import 경로 변경
from django.conf import settings  # OK
```

### Celery 태스크 미실행
```powershell
# Redis 연결 확인
redis-cli ping

# Celery worker 로그 확인
celery -A config worker -l debug
```

### 캐시 작동 안 함
```python
# Django shell에서 테스트
python manage.py shell
>>> from django.core.cache import cache
>>> cache.set('test', 'value', 60)
>>> cache.get('test')
```
