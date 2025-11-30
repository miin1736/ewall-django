# 개발 환경 가이드

## 로컬 개발 환경 실행 방법

### 1. 빠른 테스트 (Django만)
프론트엔드 개발, API 테스트만 필요한 경우:

```powershell
# 방법 1: 스크립트 사용
.\dev.ps1 start

# 방법 2: 직접 실행
.\venv\Scripts\python.exe manage.py runserver
```

**특징:**
- ✅ 즉시 시작 가능
- ✅ 웹 UI 접근: http://127.0.0.1:8000/
- ❌ 자동 크롤링 안 됨
- ❌ 백그라운드 작업 안 됨

---

### 2. 완전한 개발 환경 (Django + Celery)
백그라운드 작업, 스케줄링 테스트가 필요한 경우:

**터미널 1: Django 서버**
```powershell
.\dev.ps1 start
```

**터미널 2: Celery Worker + Beat**
```powershell
.\dev.ps1 celery
```

**사전 요구사항:**
- Redis 실행 (메시지 브로커)
  ```powershell
  # Docker 사용
  docker run -d -p 6379:6379 redis
  
  # 또는 Windows용 Redis 설치
  # https://github.com/microsoftarchive/redis/releases
  ```

**특징:**
- ✅ 자동 크롤링 (6시간마다)
- ✅ 임베딩 자동 생성 (매일 새벽 2:30)
- ✅ 가격 스냅샷 (매일 새벽 1시)
- ✅ 완전한 프로덕션 환경 시뮬레이션

---

### 3. 수동 작업 실행 (추천)

Celery 없이 Django shell에서 직접 실행:

```powershell
.\dev.ps1 shell
```

```python
# 네이버 상품 크롤링 (즉시 실행)
from apps.products.tasks import sync_naver_outlet_products
result = sync_naver_outlet_products()
print(f"✅ {result['created']}개 생성, {result['updated']}개 업데이트")

# 이미지 임베딩 생성 (10개만)
from apps.products.tasks import batch_generate_embeddings
result = batch_generate_embeddings(limit=10)
print(f"✅ {result['queued']}개 큐잉됨")

# 또는 관리 명령어 사용
exit()
```

```powershell
# 임베딩 생성
.\venv\Scripts\python.exe manage.py generate_embeddings --limit 50

# 가격 스냅샷
.\venv\Scripts\python.exe manage.py shell -c "from apps.products.tasks import snapshot_prices; snapshot_prices()"
```

**장점:**
- ✅ 즉시 실행, 즉시 결과
- ✅ 디버깅 쉬움
- ✅ Celery 불필요
- ✅ 개발 중 빠른 테스트

---

## Celery Beat 스케줄 (자동 실행)

Celery를 실행하면 다음 작업이 **자동으로** 실행됩니다:

| 작업 | 실행 주기 | 설명 |
|------|----------|------|
| 상품 크롤링 | 6시간마다 (00:00, 06:00, 12:00, 18:00) | 네이버 쇼핑 이월상품 동기화 |
| 가격 스냅샷 | 매일 01:00 | 모든 상품 가격 이력 저장 |
| **임베딩 생성** | **매일 02:30** | **누락된 이미지 임베딩 자동 생성 (100개)** |
| 가격 변동 체크 | 매시간 | 가격 하락 감지 및 알림 |
| 이메일 발송 | 5분마다 | 큐에 쌓인 이메일 발송 |
| 클릭 집계 | 매일 02:00 | 분석용 클릭 데이터 집계 |
| 캐시 워밍업 | 오전 8시, 오후 6시 | 자주 조회되는 데이터 캐싱 |

**⚠️ 중요:**
- 스케줄은 **Celery Beat가 실행 중일 때만** 작동합니다
- 로컬 개발 시 Celery를 중단하면 스케줄도 중단됩니다
- 프로덕션에서는 Docker가 24시간 실행하므로 자동 작동합니다

---

## 개발 환경별 권장 사항

### 프론트엔드 개발
```powershell
.\dev.ps1 start  # Django만
```

### 백엔드 API 개발
```powershell
.\dev.ps1 start  # Django만
```

### 크롤링/임베딩 개발
```powershell
# 터미널 1
.\dev.ps1 start

# 터미널 2
.\dev.ps1 celery

# 또는 수동 실행
.\dev.ps1 shell
>>> from apps.products.tasks import sync_naver_outlet_products
>>> sync_naver_outlet_products()
```

### 스케줄링 테스트
```powershell
# 터미널 1
.\dev.ps1 start

# 터미널 2
.\dev.ps1 celery
# Beat 로그에서 스케줄 실행 확인
```

---

## 문제 해결

### Celery 실행 시 오류
```
Error: Cannot connect to redis://localhost:6379
```
**해결:** Redis가 실행 중인지 확인
```powershell
docker run -d -p 6379:6379 redis
```

### Windows에서 Celery 오류
```
Error: Pool implementation not available
```
**해결:** `-P solo` 옵션 사용 (이미 스크립트에 포함됨)

### 스케줄이 실행 안 됨
**확인사항:**
1. Celery Beat가 실행 중인가?
2. Celery Worker가 실행 중인가?
3. Redis 연결 정상인가?

---

## 빠른 참조

```powershell
# 도움말
.\dev.ps1 help

# Django 서버
.\dev.ps1 start

# Celery (백그라운드 작업)
.\dev.ps1 celery

# Django Shell
.\dev.ps1 shell

# 마이그레이션
.\dev.ps1 migrate

# 테스트
.\dev.ps1 test
```
