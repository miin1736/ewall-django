"""
네이버 API 원본 응답 확인용 테스트 스크립트
"""
import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import requests
import json

# .env 파일 로드
BASE_DIR = Path(__file__).resolve().parent.parent
env_file = BASE_DIR / '.env.development'
load_dotenv(env_file)

# 네이버 API 설정
NAVER_CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
NAVER_CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

print(f"Client ID: {NAVER_CLIENT_ID}")
print(f"Client Secret: {NAVER_CLIENT_SECRET[:10]}...")
print()

# 네이버 쇼핑 API 호출
url = "https://openapi.naver.com/v1/search/shop.json"
headers = {
    'X-Naver-Client-Id': NAVER_CLIENT_ID,
    'X-Naver-Client-Secret': NAVER_CLIENT_SECRET,
}

# 검색어
query = "노스페이스 이월"
params = {
    'query': query,
    'display': 5,  # 5개만 테스트
    'sort': 'sim',
}

print(f"검색어: {query}")
print(f"URL: {url}")
print()

response = requests.get(url, headers=headers, params=params)

print(f"Status Code: {response.status_code}")
print()

if response.status_code == 200:
    data = response.json()
    
    print(f"총 결과 수: {data.get('total', 0)}")
    print(f"표시 개수: {data.get('display', 0)}")
    print()
    
    print("=" * 80)
    print("상품 데이터:")
    print("=" * 80)
    
    for i, item in enumerate(data.get('items', []), 1):
        print(f"\n[{i}] {item.get('title', '')[:50]}")
        print(f"    - productId: {item.get('productId', 'N/A')}")
        print(f"    - lprice: {item.get('lprice', 'N/A')} ({type(item.get('lprice')).__name__})")
        print(f"    - hprice: {item.get('hprice', 'N/A')} ({type(item.get('hprice')).__name__})")
        print(f"    - brand: {item.get('brand', 'N/A')}")
        print(f"    - maker: {item.get('maker', 'N/A')}")
        print(f"    - mallName: {item.get('mallName', 'N/A')}")
        print(f"    - image: {item.get('image', 'N/A')[:50]}...")
        print(f"    - link: {item.get('link', 'N/A')[:50]}...")
        
        # 전체 JSON 출력
        print(f"\n    전체 JSON:")
        print(f"    {json.dumps(item, ensure_ascii=False, indent=4)}")
        print("-" * 80)
    
else:
    print(f"Error: {response.text}")
