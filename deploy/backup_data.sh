#!/bin/bash
# 로컬 → 클라우드 데이터 마이그레이션 스크립트

set -e

echo "📦 로컬 데이터 백업 중..."

# 1. 데이터베이스 백업
python manage.py dumpdata \
  --natural-foreign \
  --natural-primary \
  -e contenttypes \
  -e auth.Permission \
  -e sessions \
  -e admin.LogEntry \
  > backup_$(date +%Y%m%d_%H%M%S).json

echo "✅ 백업 완료!"
echo ""
echo "클라우드 서버로 복원하려면:"
echo "1. 서버에 파일 업로드:"
echo "   scp backup_*.json user@server-ip:/var/www/ewall/"
echo ""
echo "2. 서버에서 복원:"
echo "   cd /var/www/ewall"
echo "   source venv/bin/activate"
echo "   python manage.py loaddata backup_XXXXXX.json"
