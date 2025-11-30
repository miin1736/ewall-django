# 로컬 → 클라우드 마이그레이션 체크리스트

## 배포 전 준비 ✅

### 1. 코드 준비
- [ ] Git 저장소 최신화 (`git push`)
- [ ] requirements.txt 업데이트
- [ ] .env.production 값 확인
- [ ] 민감정보 제거 (하드코딩된 키 등)

### 2. 클라우드 계정
- [ ] DigitalOcean/AWS 계정 생성
- [ ] 결제 수단 등록
- [ ] SSH 키 생성 (`ssh-keygen`)

### 3. 데이터 백업
- [ ] 로컬 DB 백업 (`python manage.py dumpdata`)
- [ ] 미디어 파일 백업 (`media/` 폴더)
- [ ] 환경변수 백업

---

## 배포 중 ⚙️

### DigitalOcean App Platform
- [ ] GitHub 저장소 연결
- [ ] 환경변수 설정
- [ ] 도메인 연결 (선택)
- [ ] 첫 배포 실행

### DigitalOcean Droplet
- [ ] Droplet 생성 (Ubuntu 22.04)
- [ ] SSH 접속 테스트
- [ ] setup_server.sh 실행
- [ ] .env.production 수정
- [ ] SSL 인증서 설치
- [ ] 도메인 DNS 설정

---

## 배포 후 검증 ✓

### 1. 기본 동작
- [ ] 웹사이트 접속 확인
- [ ] 관리자 페이지 로그인 (`/admin`)
- [ ] API 엔드포인트 테스트
- [ ] 정적 파일 로딩 확인

### 2. 데이터
- [ ] DB 연결 확인
- [ ] 백업 데이터 복원
- [ ] 미디어 파일 업로드

### 3. 성능
- [ ] 페이지 로딩 속도 (<3초)
- [ ] Redis 캐시 작동 확인
- [ ] Celery 태스크 실행 확인

### 4. 보안
- [ ] HTTPS 강제 확인
- [ ] CORS 설정 테스트
- [ ] 환경변수 노출 확인
- [ ] SQL Injection 테스트

---

## 문제 해결 🔧

### 500 에러
```bash
# 로그 확인
tail -f /var/log/ewall/gunicorn.err.log
```

**일반적 원인:**
- SECRET_KEY 미설정
- ALLOWED_HOSTS 누락
- DB 연결 실패

### 정적 파일 404
```bash
python manage.py collectstatic --noinput
sudo systemctl reload nginx
```

### Celery 작동 안 함
```bash
# Redis 연결 확인
redis-cli ping

# Worker 재시작
sudo supervisorctl restart celery-worker
```

---

## 롤백 계획 🔄

### 긴급 롤백
```bash
# 이전 버전으로 복구
git revert HEAD
git push

# 또는 수동 롤백
cd /var/www/ewall
git reset --hard <commit-hash>
sudo supervisorctl restart ewall
```

### 로컬 서버 재가동
```powershell
# 로컬에서 즉시 서버 재시작
$env:DJANGO_ENV = "development"
python manage.py runserver
```

---

## 최종 점검 📋

- [ ] 사용자 접속 가능
- [ ] 모든 페이지 정상 작동
- [ ] 가격 알림 발송 정상
- [ ] 크롤링 태스크 실행
- [ ] 에러 로그 모니터링 설정
- [ ] 백업 자동화 설정

---

## 운영 팁 💡

### 자동 백업 (crontab)
```bash
# 매일 새벽 3시 백업
0 3 * * * cd /var/www/ewall && source venv/bin/activate && python manage.py dumpdata > /backups/db_$(date +\%Y\%m\%d).json
```

### 모니터링
```bash
# 서버 상태 확인
sudo supervisorctl status

# Nginx 로그
tail -f /var/log/nginx/access.log

# 디스크 용량
df -h
```

### 업데이트
```bash
# 코드 업데이트
cd /var/www/ewall
git pull
source venv/bin/activate
pip install -r requirements.txt
python manage.py migrate
python manage.py collectstatic --noinput
sudo supervisorctl restart ewall
```
