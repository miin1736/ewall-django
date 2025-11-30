"""
Django settings for COUPANG_ACCESS_KEY and other API keys
"""
import os
from django.conf import settings

# These should be set in your .env file
COUPANG_ACCESS_KEY = os.getenv('COUPANG_ACCESS_KEY', '')
COUPANG_SECRET_KEY = os.getenv('COUPANG_SECRET_KEY', '')
LINKPRICE_API_KEY = os.getenv('LINKPRICE_API_KEY', '')
