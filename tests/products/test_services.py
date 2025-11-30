"""
Attribute extraction service tests
"""
import pytest
from apps.products.services.attribute_extractor import AttributeExtractor


class TestAttributeExtractor:
    """속성 추출 서비스 테스트"""
    
    def test_extract_down_attributes(self):
        """다운 제품 속성 추출 테스트"""
        text = "노스페이스 거위털 다운 재킷 800FP 90/10 슬림핏 나일론"
        attrs = AttributeExtractor.extract(text, 'down')
        
        assert attrs['down_type'] == 'goose'
        assert attrs['down_ratio'] == '90-10'
        assert attrs['fill_power'] == 800
        assert attrs['fit'] == 'slim'
        assert attrs['shell'] == 'nylon'
    
    def test_extract_slacks_attributes(self):
        """슬랙스 속성 추출 테스트"""
        text = "하이웨이스트 테이퍼드 슬랙스 스트레치"
        attrs = AttributeExtractor.extract(text, 'slacks')
        
        assert attrs['waist_type'] == 'high'
        assert attrs['leg_opening'] == 'tapered'
        assert attrs['stretch'] == True
    
    def test_extract_jeans_attributes(self):
        """청바지 속성 추출 테스트"""
        text = "다크워싱 스키니 청바지 로우라이즈 스트레치"
        attrs = AttributeExtractor.extract(text, 'jeans')
        
        assert attrs['wash'] == 'dark'
        assert attrs['cut'] == 'skinny'
        assert attrs['rise'] == 'low'
        assert attrs['stretch'] == True
    
    def test_extract_fill_power_various_formats(self):
        """필파워 다양한 형식 추출 테스트"""
        test_cases = [
            ("800FP 다운", 800),
            ("750 필파워", 750),
            ("900 fill", 900),
            ("650FP", 650),
        ]
        
        for text, expected in test_cases:
            attrs = AttributeExtractor.extract(text, 'down')
            assert attrs.get('fill_power') == expected
