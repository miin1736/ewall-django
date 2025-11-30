# E-wall 개발 환경 통합 관리 스크립트
param(
    [Parameter(Position=0)]
    [ValidateSet('start', 'celery', 'django', 'shell', 'migrate', 'test', 'check', 'embeddings', 'help')]
    [string]$Command = 'help'
)

function Show-Help {
    Write-Host ""
    Write-Host "E-wall 개발 도구" -ForegroundColor Green
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "사용법:" -ForegroundColor Yellow
    Write-Host "  .\dev.ps1 <command>" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "명령어:" -ForegroundColor Yellow
    Write-Host "  start       Django 서버 시작 (임베딩 자동 체크)" -ForegroundColor Cyan
    Write-Host "  django      Django 서버만 시작 (별칭)" -ForegroundColor Cyan
    Write-Host "  celery      Celery Worker + Beat 시작 (백그라운드 작업)" -ForegroundColor Cyan
    Write-Host "  shell       Django shell 실행" -ForegroundColor Cyan
    Write-Host "  migrate     마이그레이션 적용" -ForegroundColor Cyan
    Write-Host "  check       임베딩 상태 확인" -ForegroundColor Cyan
    Write-Host "  embeddings  임베딩 수동 생성" -ForegroundColor Cyan
    Write-Host "  test        테스트 실행" -ForegroundColor Cyan
    Write-Host "  help        이 도움말 표시" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "예시:" -ForegroundColor Yellow
    Write-Host "  .\dev.ps1 start       # Django 서버 시작 (자동 임베딩 체크)" -ForegroundColor Gray
    Write-Host "  .\dev.ps1 check       # 임베딩 상태 확인" -ForegroundColor Gray
    Write-Host "  .\dev.ps1 embeddings  # 임베딩 수동 생성" -ForegroundColor Gray
    Write-Host ""
    Write-Host "💡 TIP: Django 서버 시작 시" -ForegroundColor Yellow
    Write-Host "   - 자동으로 임베딩 상태를 체크합니다" -ForegroundColor Cyan
    Write-Host "   - 누락된 임베딩은 백그라운드에서 자동 생성됩니다 (최대 50개)" -ForegroundColor Cyan
    Write-Host "===============================================" -ForegroundColor Green
    Write-Host ""
}

switch ($Command) {
    'start' {
        Write-Host "🚀 Starting Django Development Server..." -ForegroundColor Green
        Write-Host "   - 자동 임베딩 체크 활성화됨" -ForegroundColor Cyan
        Write-Host ""
        .\venv\Scripts\python.exe manage.py runserver
    }
    'django' {
        Write-Host "🚀 Starting Django Development Server..." -ForegroundColor Green
        Write-Host "   - 자동 임베딩 체크 활성화됨" -ForegroundColor Cyan
        Write-Host ""
        .\venv\Scripts\python.exe manage.py runserver
    }
    'celery' {
        Write-Host "🔧 Starting Celery Worker + Beat..." -ForegroundColor Green
        Write-Host "⚠️  Make sure Redis is running!" -ForegroundColor Yellow
        Write-Host ""
        .\venv\Scripts\celery.exe -A config worker -l info -P solo --beat
    }
    'shell' {
        Write-Host "🐚 Starting Django Shell..." -ForegroundColor Green
        .\venv\Scripts\python.exe manage.py shell
    }
    'migrate' {
        Write-Host "🗄️  Running migrations..." -ForegroundColor Green
        .\venv\Scripts\python.exe manage.py migrate
    }
    'check' {
        Write-Host "🔍 Checking embedding status..." -ForegroundColor Green
        .\venv\Scripts\python.exe manage.py check_embeddings
    }
    'embeddings' {
        Write-Host "🎨 Generating embeddings..." -ForegroundColor Green
        Write-Host "   (최대 100개 처리)" -ForegroundColor Cyan
        Write-Host ""
        .\venv\Scripts\python.exe manage.py generate_embeddings --limit 100
    }
    'test' {
        Write-Host "🧪 Running tests..." -ForegroundColor Green
        .\venv\Scripts\python.exe manage.py test
    }
    'help' {
        Show-Help
    }
    default {
        Show-Help
    }
}
