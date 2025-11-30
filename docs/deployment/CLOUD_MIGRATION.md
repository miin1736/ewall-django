# E-wall 클라우드 마이그레이션 가이드

## 🎯 전략: 로컬 → 클라우드 무중단 전환

### 준비 완료 ✅
- 환경별 설정 분리 (development/production)
- 환경변수 기반 구성
- PostgreSQL/Redis 지원
- Gunicorn/Nginx 준비

---

## 방법 1: DigitalOcean App Platform (가장 쉬움) ⭐⭐⭐⭐⭐

### 소요 시간: 30분
### 월 비용: $12~$24
### 난이도: ★☆☆☆☆

```bash
# 1. Git 저장소 연결만 하면 자동 배포
# 2. PostgreSQL/Redis 자동 프로비저닝
# 3. SSL 인증서 자동 발급
# 4. 오토 스케일링 지원
```

### 단계
1. **DigitalOcean 계정 생성**
   - https://www.digitalocean.com 가입

2. **App Platform 선택**
   - "Create" → "App Platform"
   - GitHub 저장소 연결

3. **환경변수 설정**
   ```
   DJANGO_ENV=production
   SECRET_KEY=<자동생성>
   DATABASE_URL=<자동생성>
   REDIS_URL=<자동생성>
   ```

4. **배포!**
   - "Deploy" 클릭
   - 5-10분 후 자동 배포 완료

### 장점
- ✅ Git push만 하면 자동 배포
- ✅ DB/Redis 자동 관리
- ✅ SSL 자동 갱신
- ✅ 모니터링 내장
- ✅ 롤백 원클릭

### 단점
- ⚠️ 커스터마이징 제한
- ⚠️ 가격이 VPS보다 높음

---

## 방법 2: DigitalOcean Droplet (가성비 최고) ⭐⭐⭐⭐

### 소요 시간: 1-2시간
### 월 비용: $6~$24
### 난이도: ★★☆☆☆

### 자동 배포 스크립트 (아래 파일들 생성됨)

```bash
# 1. Droplet 생성 (Ubuntu 22.04)
# 2. 아래 스크립트 실행
chmod +x deploy/setup_server.sh
./deploy/setup_server.sh
```

### 장점
- ✅ 저렴한 비용
- ✅ 완전한 제어권
- ✅ 여러 프로젝트 호스팅 가능

### 단점
- ⚠️ 초기 설정 필요
- ⚠️ 보안 업데이트 직접 관리

---

## 방법 3: AWS Lightsail (중간) ⭐⭐⭐

### 소요 시간: 2시간
### 월 비용: $10~$40
### 난이도: ★★★☆☆

### 특징
- AWS 생태계 진입점
- 예측 가능한 가격
- 스냅샷/백업 쉬움

---

## 🔄 마이그레이션 프로세스

### Phase 1: 준비 (로컬)
```powershell
# 1. Git 저장소 확인
git remote -v

# 2. 필수 파일 추가
git add deploy/
git commit -m "Add deployment configs"
git push
```

### Phase 2: 클라우드 설정
```bash
# 서버에서 실행
git clone https://github.com/yourusername/ewall-django.git
cd ewall-django
./deploy/setup_server.sh
```

### Phase 3: 데이터 마이그레이션
```powershell
# 로컬 데이터 백업
python manage.py dumpdata --natural-foreign --natural-primary \
  -e contenttypes -e auth.Permission > backup.json

# 서버로 전송
scp backup.json user@server:/path/to/ewall-django/

# 서버에서 복원
python manage.py loaddata backup.json
```

### Phase 4: DNS 전환
```
# 기존 로컬: localhost:8000
# 1. 서버 테스트: http://your-server-ip
# 2. DNS 설정: yourdomain.com → server-ip
# 3. SSL 적용
# 4. 로컬 서버 종료
```

---

## 📊 서비스별 비교

| 서비스 | 난이도 | 월비용 | 설정시간 | 확장성 | 추천도 |
|--------|--------|--------|----------|--------|--------|
| **DigitalOcean App** | ⭐ | $12-24 | 30분 | 자동 | ⭐⭐⭐⭐⭐ |
| **DO Droplet** | ⭐⭐ | $6-24 | 1-2시간 | 수동 | ⭐⭐⭐⭐ |
| **AWS Lightsail** | ⭐⭐⭐ | $10-40 | 2시간 | 수동 | ⭐⭐⭐ |
| **Heroku** | ⭐ | $25-50 | 20분 | 자동 | ⭐⭐⭐ |
| **AWS EC2+RDS** | ⭐⭐⭐⭐ | $30+ | 4-6시간 | 완전 | ⭐⭐ |

---

## 🎁 보너스: 무중단 전환 전략

### 방법: 듀얼 운영
```
주간: 로컬 서버 (테스트 겸)
야간: 클라우드 서버

→ 2주 후 완전 전환
```

### 체크리스트
- [ ] 클라우드 서버 설치
- [ ] 데이터 동기화 (rsync/cron)
- [ ] 성능 테스트
- [ ] DNS TTL 낮춤 (300초)
- [ ] DNS 전환
- [ ] 모니터링 확인
- [ ] 로컬 서버 백업 유지

---

## 💰 비용 시뮬레이션

### 사용자 100명
- **DigitalOcean App**: $12/월
- **Droplet (Basic)**: $6/월
- **데이터 전송**: ~$1/월
- **합계**: $7-13/월

### 사용자 1,000명
- **DigitalOcean App**: $24/월
- **Droplet (4GB)**: $24/월
- **PostgreSQL**: $15/월
- **Redis**: $10/월
- **합계**: $49/월

### 사용자 10,000명
- **Load Balancer**: $12/월
- **Droplets x3**: $72/월
- **Managed DB**: $60/월
- **Redis Cluster**: $30/월
- **합계**: $174/월

---

## ⚡ 즉시 시작 가이드

### 1분 만에 배포 준비
```powershell
# 배포 스크립트 생성
New-Item -ItemType Directory -Path deploy -Force

# GitHub Actions 자동 배포 설정
New-Item -ItemType Directory -Path .github\workflows -Force
```

### Git Push = 자동 배포
```bash
# 코드 수정
git add .
git commit -m "Update feature"
git push

# → 자동으로 클라우드에 배포됨!
```

---

## 🆘 문제 해결

### Q: 로컬 DB 데이터를 클라우드로 옮기려면?
```powershell
# 1. 로컬 백업
python manage.py dumpdata > data.json

# 2. 클라우드 업로드
scp data.json user@server:/app/

# 3. 클라우드에서 복원
python manage.py loaddata data.json
```

### Q: 배포 후 500 에러
```bash
# 로그 확인
tail -f logs/error.log

# 일반적 원인
# 1. SECRET_KEY 미설정
# 2. ALLOWED_HOSTS 누락
# 3. DB 연결 실패
```

### Q: 정적 파일 안 보임
```bash
# collectstatic 실행
python manage.py collectstatic --noinput

# Nginx 설정 확인
nginx -t
systemctl reload nginx
```

---

## 🎯 추천 선택

### 처음 시작 (사용자 <500명)
→ **DigitalOcean App Platform** ($12/월)
- 클릭 몇 번으로 완료
- 관리 부담 최소

### 비용 절약 (사용자 <2,000명)
→ **DigitalOcean Droplet** ($6-12/월)
- 가성비 최고
- 약간의 학습 필요

### 확장 계획 (사용자 >5,000명)
→ **AWS Lightsail → EC2 전환**
- 처음엔 Lightsail로 시작
- 성장하면 EC2로 마이그레이션
