# 프로젝트 파일 정리 완료

## 삭제된 파일

### 1. 임시 스크립트 (13개)
개발 중 테스트/디버깅 용도로 생성된 일회성 스크립트들:

- `check_brand_slugs.py` - 브랜드 slug 검증 (기능이 apps/products/management/commands/로 이동)
- `check_status.py` - 상태 체크 스크립트
- `cleanup_brands.py` - 브랜드 정리 스크립트
- `fix_brand_slugs.py` - 브랜드 slug 수정 스크립트 (작업 완료)
- `reclassify_generic.py` - 카테고리 재분류 스크립트
- `reclassify_with_ai.py` - AI 기반 재분류 스크립트
- `test_slug_logic.py` - Slug 로직 테스트
- `test_automation.py` - 자동화 테스트
- `test_faiss_index.py` - Faiss 인덱스 테스트
- `test_naver_api.py` - 네이버 API 테스트
- `test_naver_brand.py` - 네이버 브랜드 테스트
- `test_texture_api.py` - 텍스처 API 테스트
- `data_backup.json` - 임시 백업 파일

**대체:** `dev.ps1 shell` 또는 Django management commands 사용

---

### 2. 배치/셸 스크립트 (6개)
dev.ps1로 통합되어 불필요해진 스크립트들:

- `server_control.bat` - 서버 제어 배치 파일
- `start_automation.bat` - Celery 자동화 시작 스크립트
- `stop_automation.bat` - Celery 중지 스크립트
- `run_celery_dev.ps1` - Celery 개발 실행 스크립트
- `run_django_dev.ps1` - Django 개발 실행 스크립트
- `setup.ps1` - 초기 설정 스크립트

**대체:** `dev.ps1` (통합 개발 도구)

---

### 3. 중복 문서 (1개)

- `AUTOMATION_GUIDE.md` - 자동화 가이드 (DEVELOPMENT.md에 통합)

**대체:** `DEVELOPMENT.md`

---

### 4. 빌드 및 캐시 파일

- `build.log` - 빌드 로그
- `celerybeat-schedule` - Celery Beat 스케줄 캐시
- `.coverage` - 테스트 커버리지 데이터
- `.pytest_cache/` - Pytest 캐시
- `htmlcov/` - 커버리지 HTML 리포트
- `__pycache__/` - Python 바이트코드 캐시 (전체)

**참고:** 이 파일들은 .gitignore에 포함되어 자동 제외됨

---

## 유지된 핵심 파일

### 루트 디렉토리
```
ewall-django/
├── dev.ps1                 # 통합 개발 도구 ⭐
├── manage.py               # Django 관리 스크립트
├── conftest.py             # Pytest 설정
├── README.md               # 프로젝트 개요
├── DEVELOPMENT.md          # 개발 가이드
├── requirements.txt        # 의존성
├── docker-compose.yml      # Docker 구성
└── Dockerfile              # Docker 이미지
```

### 개발 도구 (dev.ps1)

**사용법:**
```powershell
.\dev.ps1 start       # Django 서버 시작
.\dev.ps1 celery      # Celery 시작
.\dev.ps1 shell       # Django Shell
.\dev.ps1 migrate     # 마이그레이션
.\dev.ps1 check       # 임베딩 상태 확인
.\dev.ps1 embeddings  # 임베딩 생성
.\dev.ps1 help        # 도움말
```

---

## 구조 개선 사항

### Before (정리 전)
```
ewall-django/
├── ❌ check_brand_slugs.py
├── ❌ fix_brand_slugs.py
├── ❌ test_*.py (10개)
├── ❌ server_control.bat
├── ❌ start_automation.bat
├── ❌ run_*.ps1 (3개)
├── ❌ AUTOMATION_GUIDE.md
├── ✅ dev.ps1
├── ✅ README.md
└── ...
```

### After (정리 후)
```
ewall-django/
├── ✅ dev.ps1              # 통합 도구
├── ✅ README.md
├── ✅ DEVELOPMENT.md
├── ✅ manage.py
├── ✅ conftest.py
└── ...
```

---

## 향후 관리 지침

### 1. 임시 파일 생성 규칙
임시 스크립트는 다음 패턴으로 생성:
- `temp_*.py` - 임시 테스트
- `debug_*.py` - 디버깅 용도

이러한 파일들은 `.gitignore`에서 자동 제외됩니다.

### 2. 영구 기능 추가 시
새로운 기능은 적절한 위치에:
- **Management Commands**: `apps/*/management/commands/`
- **유틸리티**: `apps/*/utils/`
- **스크립트**: `scripts/`

### 3. 문서 관리
- **개발 가이드**: `DEVELOPMENT.md`
- **기능별 문서**: `docs/`
- **배포 문서**: `deploy/`, `docs/deployment/`

---

## .gitignore 업데이트

다음 패턴이 추가되었습니다:

```gitignore
# Temporary/Debug files
/test_*.py
/debug_*.py
/check_*.py
/cleanup_*.py
/fix_*.py
/reclassify_*.py
*_temp.py
*_backup.py
*_backup.json

# Old shell scripts
server_control.bat
start_automation.bat
stop_automation.bat
run_*.ps1
setup.ps1
```

---

## 정리 효과

### 파일 수 감소
- 임시 스크립트: -13개
- 배치/셸: -6개
- 문서: -1개
- **총 -20개 파일**

### 구조 명확화
- ✅ 개발 도구 통합 (`dev.ps1`)
- ✅ 문서 체계화 (`docs/`)
- ✅ 루트 디렉토리 간소화

### 유지보수성 향상
- ✅ 중복 제거
- ✅ 명확한 역할 분담
- ✅ 자동 캐시 정리 (.gitignore)

---

**정리 완료 일시:** 2025-11-30
