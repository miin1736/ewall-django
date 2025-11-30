"""
Django Settings Module
환경 자동 선택: DJANGO_ENV 환경변수 기반
"""
import os

env = os.environ.get('DJANGO_ENV', 'development')

if env == 'production':
    from .production import *
    print("🚀 Django running in: PRODUCTION mode")
elif env == 'testing':
    from .testing import *
    print("🧪 Django running in: TESTING mode")
else:
    from .development import *
    print("🛠️  Django running in: DEVELOPMENT mode")
