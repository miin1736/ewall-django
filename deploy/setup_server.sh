#!/bin/bash
# DigitalOcean Droplet 자동 설정 스크립트

set -e

echo "🚀 E-wall Django 서버 설정 시작..."

# 1. 시스템 업데이트
echo "📦 시스템 패키지 업데이트..."
sudo apt-get update
sudo apt-get upgrade -y

# 2. Python 및 필수 도구 설치
echo "🐍 Python 3.11 설치..."
sudo apt-get install -y python3.11 python3.11-venv python3-pip
sudo apt-get install -y build-essential libpq-dev nginx supervisor git

# 3. PostgreSQL 설치
echo "🐘 PostgreSQL 설치..."
sudo apt-get install -y postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql

# PostgreSQL 데이터베이스 생성
sudo -u postgres psql <<EOF
CREATE DATABASE ewall_prod;
CREATE USER ewall_user WITH PASSWORD 'change_this_password';
ALTER ROLE ewall_user SET client_encoding TO 'utf8';
ALTER ROLE ewall_user SET default_transaction_isolation TO 'read committed';
ALTER ROLE ewall_user SET timezone TO 'Asia/Seoul';
GRANT ALL PRIVILEGES ON DATABASE ewall_prod TO ewall_user;
\q
EOF

# 4. Redis 설치
echo "📮 Redis 설치..."
sudo apt-get install -y redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server

# 5. 프로젝트 디렉토리 생성
echo "📁 프로젝트 디렉토리 설정..."
sudo mkdir -p /var/www/ewall
sudo chown -R $USER:$USER /var/www/ewall

# 6. Git 저장소 클론 (수동으로 실행 필요)
echo "📥 Git 저장소를 클론하세요:"
echo "cd /var/www && git clone https://github.com/yourusername/ewall-django.git ewall"

# 7. Python 가상환경 생성
echo "🔧 Python 가상환경 생성..."
cd /var/www/ewall
python3.11 -m venv venv
source venv/bin/activate

# 8. Python 패키지 설치
echo "📚 Python 패키지 설치..."
pip install --upgrade pip
pip install -r requirements.txt

# 9. 환경변수 파일 생성
echo "🔐 환경변수 파일 생성..."
cat > /var/www/ewall/.env.production <<EOF
DJANGO_ENV=production
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
DATABASE_URL=postgresql://ewall_user:change_this_password@localhost/ewall_prod
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
ALLOWED_HOSTS=your-domain.com,www.your-domain.com,$(curl -s ifconfig.me)
CORS_ORIGINS=https://your-domain.com
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-app-password
ADMIN_EMAIL=admin@your-domain.com
EOF

echo "⚠️  /var/www/ewall/.env.production 파일을 실제 값으로 수정하세요!"

# 10. Django 설정
echo "🎨 Django 초기화..."
python manage.py collectstatic --noinput
python manage.py migrate

# 11. Gunicorn 설정
echo "🦄 Gunicorn 설정..."
sudo tee /etc/supervisor/conf.d/ewall.conf > /dev/null <<EOF
[program:ewall]
directory=/var/www/ewall
command=/var/www/ewall/venv/bin/gunicorn config.wsgi:application --bind 127.0.0.1:8000 --workers 4 --timeout 30
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/ewall/gunicorn.err.log
stdout_logfile=/var/log/ewall/gunicorn.out.log
environment=DJANGO_ENV="production"

[program:celery-worker]
directory=/var/www/ewall
command=/var/www/ewall/venv/bin/celery -A config worker -l info
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/ewall/celery.err.log
stdout_logfile=/var/log/ewall/celery.out.log

[program:celery-beat]
directory=/var/www/ewall
command=/var/www/ewall/venv/bin/celery -A config beat -l info
user=$USER
autostart=true
autorestart=true
stderr_logfile=/var/log/ewall/celery-beat.err.log
stdout_logfile=/var/log/ewall/celery-beat.out.log
EOF

# 로그 디렉토리 생성
sudo mkdir -p /var/log/ewall
sudo chown -R $USER:$USER /var/log/ewall

# 12. Nginx 설정
echo "🌐 Nginx 설정..."
sudo tee /etc/nginx/sites-available/ewall > /dev/null <<'EOF'
upstream ewall_app {
    server 127.0.0.1:8000;
}

# HTTP → HTTPS 리다이렉트
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    location /.well-known/acme-challenge/ {
        root /var/www/certbot;
    }
    
    location / {
        return 301 https://$server_name$request_uri;
    }
}

# HTTPS 서버
server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL 인증서 (Let's Encrypt)
    # ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    # ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    client_max_body_size 10M;
    
    # 정적 파일
    location /static/ {
        alias /var/www/ewall/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }
    
    location /media/ {
        alias /var/www/ewall/media/;
        expires 7d;
    }
    
    # Django 앱
    location / {
        proxy_pass http://ewall_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
    }
    
    # 보안 헤더
    add_header X-Frame-Options "DENY" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
}
EOF

# Nginx 활성화
sudo ln -sf /etc/nginx/sites-available/ewall /etc/nginx/sites-enabled/
sudo rm -f /etc/nginx/sites-enabled/default
sudo nginx -t

# 13. 서비스 시작
echo "🎬 서비스 시작..."
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start ewall celery-worker celery-beat
sudo systemctl restart nginx

# 14. 방화벽 설정
echo "🔒 방화벽 설정..."
sudo ufw allow 'Nginx Full'
sudo ufw allow OpenSSH
sudo ufw --force enable

# 15. SSL 인증서 설치 안내
echo ""
echo "✅ 기본 설정 완료!"
echo ""
echo "다음 단계:"
echo "1. /var/www/ewall/.env.production 파일 수정"
echo "2. SSL 인증서 설치:"
echo "   sudo apt-get install certbot python3-certbot-nginx"
echo "   sudo certbot --nginx -d your-domain.com -d www.your-domain.com"
echo "3. Nginx 설정 파일에서 도메인 변경: /etc/nginx/sites-available/ewall"
echo "4. 서비스 재시작: sudo supervisorctl restart all && sudo systemctl reload nginx"
echo "5. 서버 접속: http://$(curl -s ifconfig.me)"
echo ""
echo "🎉 배포 준비 완료!"
