"""
Django Testing Settings
"""
from .base import *

DEBUG = False
SECRET_KEY = 'test-secret-key'
ALLOWED_HOSTS = ['testserver', 'localhost']

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}

CACHES = {'default': {'BACKEND': 'django.core.cache.backends.dummy.DummyCache'}}
CORS_ALLOW_ALL_ORIGINS = True
EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
CELERY_TASK_ALWAYS_EAGER = True
REST_FRAMEWORK['DEFAULT_THROTTLE_RATES'] = {'anon': '10000/hour', 'user': '10000/hour'}
AUTH_PASSWORD_VALIDATORS = []
LOGGING = {'version': 1, 'disable_existing_loggers': True}

print("🧪 Testing settings loaded")
