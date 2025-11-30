# E-wall Django 설치 가이드

## ⚠️ 필수 소프트웨어 설치 필요

프로젝트를 실행하기 전에 다음 소프트웨어를 설치해야 합니다:

## 1. Python 3.11+ 설치

### 방법 1: 공식 Python 다운로드 (권장)

1. [Python 공식 웹사이트](https://www.python.org/downloads/) 방문
2. "Download Python 3.11.x" 또는 최신 버전 다운로드
3. 설치 프로그램 실행 시 **반드시 "Add Python to PATH" 체크박스 선택**
4. "Install Now" 클릭

### 방법 2: Microsoft Store

1. Windows 시작 메뉴에서 "Microsoft Store" 실행
2. "Python 3.11" 검색
3. 설치 클릭

### 설치 확인

```powershell
python --version
# 또는
py --version
```

출력 예시: `Python 3.11.x`

## 2. Docker Desktop 설치 (선택사항이지만 강력 권장)

### Docker Desktop for Windows

1. [Docker Desktop 다운로드](https://www.docker.com/products/docker-desktop/)
2. 설치 프로그램 실행
3. WSL 2 백엔드 사용 (권장)
4. 설치 후 시스템 재시작
5. Docker Desktop 실행

### 설치 확인

```powershell
docker --version
docker-compose --version
```

출력 예시:
```
Docker version 24.0.x
Docker Compose version v2.x.x
```

## 3. Git 설치 확인 (이미 설치되어 있을 가능성 높음)

```powershell
git --version
```

설치되어 있지 않다면:
1. [Git for Windows 다운로드](https://git-scm.com/download/win)
2. 설치 프로그램 실행

---

## 설치 후 프로젝트 실행

### 옵션 A: Docker Compose 사용 (가장 간단)

```powershell
# 1. 환경 변수 파일 생성
Copy-Item .env.example .env

# 2. 전체 스택 실행
docker-compose up -d

# 3. 데이터베이스 마이그레이션
docker-compose exec web python manage.py migrate

# 4. 슈퍼유저 생성
docker-compose exec web python manage.py createsuperuser

# 5. 샘플 데이터 생성
docker-compose exec web python manage.py create_sample_data

# 6. 브라우저에서 확인
# http://localhost:8000
```

### 옵션 B: 로컬 Python 환경 사용

#### 전제 조건
- PostgreSQL 15+ 설치 및 실행 중
- Redis 7+ 설치 및 실행 중

```powershell
# 1. 가상 환경 생성
python -m venv venv
.\venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install -r requirements\base.txt

# 3. 환경 변수 설정
Copy-Item .env.example .env
# .env 파일 편집하여 데이터베이스 정보 입력

# 4. 마이그레이션
python manage.py migrate

# 5. 슈퍼유저 생성
python manage.py createsuperuser

# 6. 샘플 데이터 생성
python manage.py create_sample_data

# 7. 서버 실행
python manage.py runserver
```

### PostgreSQL과 Redis를 Docker로만 실행 (추천)

Python은 로컬에 설치하되, 데이터베이스는 Docker로 실행:

```powershell
# PostgreSQL 실행
docker run -d --name ewall-db `
  -e POSTGRES_DB=ewall `
  -e POSTGRES_USER=ewall `
  -e POSTGRES_PASSWORD=password `
  -p 5432:5432 `
  postgres:15

# Redis 실행
docker run -d --name ewall-redis `
  -p 6379:6379 `
  redis:7

# 이후 위의 "옵션 B" 단계 진행
```

---

## 다음 단계

필수 소프트웨어 설치가 완료되면:

1. **Docker 사용**: `docker-compose up -d` 명령으로 즉시 실행
2. **로컬 Python 사용**: `QUICKSTART.md`의 "방법 2: 수동 설정" 참조
3. **자동 설정**: `setup.ps1` 스크립트 실행

---

## 문제 해결

### Python 설치 후 "python" 명령이 작동하지 않는 경우

1. PowerShell을 완전히 종료하고 다시 실행
2. 시스템 재시작
3. 환경 변수 PATH에 Python이 있는지 확인:
   ```powershell
   $env:PATH -split ';' | Select-String python
   ```

### Docker Desktop이 시작되지 않는 경우

1. WSL 2 설치 확인:
   ```powershell
   wsl --update
   ```
2. Hyper-V 활성화 (Windows 10 Pro/Enterprise):
   - 제어판 → 프로그램 → Windows 기능 켜기/끄기
   - "Hyper-V" 체크
   - 재시작

### 포트 충돌 오류

다른 프로그램이 이미 사용 중인 포트:
- PostgreSQL: 5432
- Redis: 6379
- Django: 8000
- Nginx: 80

해결:
1. 실행 중인 프로그램 종료
2. 또는 `docker-compose.yml`에서 포트 번호 변경

---

## 요약

최소 요구사항:
- ✅ **Python 3.11+** (필수)
- ✅ **Docker Desktop** (강력 권장)
- ✅ **Git** (선택)

설치 순서:
1. Python 설치 → 재시작
2. Docker Desktop 설치 → 재시작
3. `docker-compose up -d` 실행
4. 브라우저에서 http://localhost:8000 접속

**문제가 계속되면 이슈를 등록해주세요!**
