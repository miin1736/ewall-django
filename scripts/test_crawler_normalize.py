"""
크롤러 정규화 테스트
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(BASE_DIR))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.development')

import django
django.setup()

from apps.products.services.crawlers.naver_shopping_crawler import NaverShoppingCrawler

# 테스트용 샘플 데이터 (실제 네이버 API 응답 형식)
sample_items = [
    {
        "title": "노스페이스 이월할인 남여공용집업 시드 테크 트레이닝 자켓",
        "lprice": "62100",  # 문자열
        "hprice": "",       # 빈 문자열
        "productId": "89665871422",
        "brand": "노스페이스",
        "image": "https://example.com/image.jpg",
        "link": "https://example.com/product",
        "mallName": "테스트몰"
    },
    {
        "title": "파타고니아 레트로 X 자켓",
        "lprice": "280000",
        "hprice": "350000",
        "productId": "12345678",
        "brand": "파타고니아",
        "image": "https://example.com/image2.jpg",
        "link": "https://example.com/product2",
        "mallName": "테스트몰2"
    }
]

crawler = NaverShoppingCrawler()

print("=" * 80)
print("크롤러 정규화 테스트")
print("=" * 80)
print()

for i, item in enumerate(sample_items, 1):
    print(f"[{i}] 원본 데이터:")
    print(f"    title: {item['title']}")
    print(f"    lprice: {repr(item['lprice'])} (type: {type(item['lprice']).__name__})")
    print(f"    hprice: {repr(item['hprice'])} (type: {type(item['hprice']).__name__})")
    print()

normalized = crawler._normalize(sample_items)

print("=" * 80)
print("정규화 결과:")
print("=" * 80)
print()

for i, result in enumerate(normalized, 1):
    print(f"[{i}] {result['title']}")
    print(f"    price: {result['price']:,}원")
    print(f"    original_price: {result['original_price']:,}원" if result['original_price'] else "    original_price: None")
    print(f"    discount_rate: {result['discount_rate']}%")
    print()
