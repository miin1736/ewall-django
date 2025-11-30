"""
네이버 쇼핑 검색 API 응답 데이터 구조 확인
실행: python scripts/check_naver_api_response.py
"""
import requests
import json
import os
from dotenv import load_dotenv

# 환경변수 로드
load_dotenv('.env.development')

CLIENT_ID = os.getenv('NAVER_CLIENT_ID')
CLIENT_SECRET = os.getenv('NAVER_CLIENT_SECRET')

def test_naver_api():
    """네이버 쇼핑 API 테스트 및 응답 구조 확인"""
    
    url = "https://openapi.naver.com/v1/search/shop.json"
    
    headers = {
        'X-Naver-Client-Id': CLIENT_ID,
        'X-Naver-Client-Secret': CLIENT_SECRET
    }
    
    params = {
        'query': '노스페이스 다운',
        'display': 3,  # 3개만 가져오기
        'sort': 'sim'
    }
    
    print("="*80)
    print("네이버 쇼핑 검색 API 테스트")
    print("="*80)
    print(f"\n검색어: {params['query']}")
    print(f"요청 URL: {url}")
    print(f"\n요청 중...\n")
    
    response = requests.get(url, headers=headers, params=params)
    
    if response.status_code == 200:
        data = response.json()
        
        print("✅ API 호출 성공!\n")
        print("-"*80)
        print("전체 응답 구조:")
        print("-"*80)
        print(f"total: {data.get('total')}개 (전체 검색 결과 수)")
        print(f"start: {data.get('start')} (검색 시작 위치)")
        print(f"display: {data.get('display')} (한 번에 표시할 검색 결과 개수)")
        print(f"items: {len(data.get('items', []))}개 (실제 반환된 상품 수)")
        
        print("\n" + "="*80)
        print("개별 상품 정보 (items 배열 내부)")
        print("="*80)
        
        for idx, item in enumerate(data.get('items', []), 1):
            print(f"\n📦 상품 #{idx}")
            print("-"*80)
            
            # 모든 필드 출력
            fields = [
                ('title', '상품명 (HTML 태그 포함)', item.get('title')),
                ('link', '상품 URL (구매 링크)', item.get('link')),
                ('image', '상품 이미지 URL', item.get('image')),
                ('lprice', '최저가 (네이버 기준)', f"{int(item.get('lprice', 0)):,}원"),
                ('hprice', '최고가 (원가)', f"{int(item.get('hprice', 0)):,}원" if item.get('hprice') else "미제공"),
                ('mallName', '쇼핑몰 이름', item.get('mallName')),
                ('productId', '상품 ID', item.get('productId')),
                ('productType', '상품 유형', f"{item.get('productType')} (1:일반, 2:중고, 3:단종, 4:판매예정)"),
                ('brand', '브랜드', item.get('brand') or '미제공'),
                ('maker', '제조사', item.get('maker') or '미제공'),
                ('category1', '대분류 카테고리', item.get('category1') or '미제공'),
                ('category2', '중분류 카테고리', item.get('category2') or '미제공'),
                ('category3', '소분류 카테고리', item.get('category3') or '미제공'),
                ('category4', '세분류 카테고리', item.get('category4') or '미제공'),
            ]
            
            for key, description, value in fields:
                print(f"{key:15} : {description}")
                print(f"{'':15}   → {value}")
            
            # 할인율 계산
            lprice = int(item.get('lprice', 0))
            hprice = int(item.get('hprice', lprice))
            if hprice > lprice > 0:
                discount = int(((hprice - lprice) / hprice) * 100)
                print(f"{'할인율':15} : {discount}% OFF")
        
        print("\n" + "="*80)
        print("전체 JSON 응답 (참고용)")
        print("="*80)
        print(json.dumps(data, indent=2, ensure_ascii=False))
        
    else:
        print(f"❌ API 호출 실패!")
        print(f"상태 코드: {response.status_code}")
        print(f"응답: {response.text}")
        
        if response.status_code == 401:
            print("\n⚠️  인증 오류:")
            print("   - NAVER_CLIENT_ID 확인")
            print("   - NAVER_CLIENT_SECRET 확인")
        elif response.status_code == 429:
            print("\n⚠️  API 호출 제한 초과:")
            print("   - 일 25,000건 제한")


if __name__ == '__main__':
    if not CLIENT_ID or not CLIENT_SECRET:
        print("❌ 환경변수가 설정되지 않았습니다!")
        print("\n.env.development 파일을 확인하세요:")
        print("NAVER_CLIENT_ID=your-client-id")
        print("NAVER_CLIENT_SECRET=your-client-secret")
    else:
        test_naver_api()
