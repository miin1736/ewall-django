"""
Attribute Extractor Service
텍스트에서 상품 속성을 추출하는 서비스
"""
import re
from typing import Dict, Any, Optional


class AttributeExtractor:
    """텍스트에서 상품 속성 추출"""
    
    # 정규식 패턴 정의
    PATTERNS = {
        'down_type': {
            'goose': re.compile(r'거위|goose|구스', re.IGNORECASE),
            'duck': re.compile(r'오리|duck|덕', re.IGNORECASE),
            'synthetic': re.compile(r'합성|synthetic|프리마로프트|primaloft', re.IGNORECASE),
        },
        'down_ratio': {
            '90-10': re.compile(r'90[/-]10|90/10|90-10'),
            '80-20': re.compile(r'80[/-]20|80/20|80-20'),
            '70-30': re.compile(r'70[/-]30|70/30|70-30'),
            '60-40': re.compile(r'60[/-]40|60/40|60-40'),
        },
        'fill_power': re.compile(r'(\d{3,4})\s*(?:fp|fill|필파워|필|FP)', re.IGNORECASE),
        'hood': {
            True: re.compile(r'후드|hood|hooded', re.IGNORECASE),
            False: re.compile(r'노후드|no hood|hoodless|without hood', re.IGNORECASE),
        },
        'fit': {
            'slim': re.compile(r'슬림|slim|fitted|타이트', re.IGNORECASE),
            'regular': re.compile(r'레귤러|regular|classic|standard|일반', re.IGNORECASE),
            'relaxed': re.compile(r'릴렉스|relaxed|loose|루즈', re.IGNORECASE),
            'oversized': re.compile(r'오버사이즈|oversized|큰|빅|big', re.IGNORECASE),
        },
        'shell': {
            'nylon': re.compile(r'나일론|nylon', re.IGNORECASE),
            'polyester': re.compile(r'폴리에스터|polyester', re.IGNORECASE),
            'gore-tex': re.compile(r'고어텍스|gore-?tex', re.IGNORECASE),
            'cotton': re.compile(r'코튼|cotton|면', re.IGNORECASE),
            'wool': re.compile(r'울|wool|양모', re.IGNORECASE),
        },
        'waist_type': {
            'high': re.compile(r'하이웨이스트|high waist|high-rise|하이라이즈', re.IGNORECASE),
            'mid': re.compile(r'미드웨이스트|mid waist|mid-rise|미드라이즈|regular', re.IGNORECASE),
            'low': re.compile(r'로우웨이스트|low waist|low-rise|로우라이즈', re.IGNORECASE),
        },
        'leg_opening': {
            'tapered': re.compile(r'테이퍼드|tapered|슬림|slim', re.IGNORECASE),
            'straight': re.compile(r'스트레이트|straight', re.IGNORECASE),
            'wide': re.compile(r'와이드|wide|넓은', re.IGNORECASE),
        },
        'wash': {
            'light': re.compile(r'라이트|light|밝은|연한', re.IGNORECASE),
            'medium': re.compile(r'미디엄|medium|중간', re.IGNORECASE),
            'dark': re.compile(r'다크|dark|어두운|진한', re.IGNORECASE),
            'black': re.compile(r'블랙|black|검정', re.IGNORECASE),
        },
        'cut': {
            'skinny': re.compile(r'스키니|skinny', re.IGNORECASE),
            'slim': re.compile(r'슬림|slim', re.IGNORECASE),
            'straight': re.compile(r'스트레이트|straight', re.IGNORECASE),
            'bootcut': re.compile(r'부츠컷|bootcut|boot cut', re.IGNORECASE),
            'wide': re.compile(r'와이드|wide', re.IGNORECASE),
        },
        'neckline': {
            'crew': re.compile(r'크루넥|crew neck|크루', re.IGNORECASE),
            'mock': re.compile(r'목넥|mock neck|모크넥', re.IGNORECASE),
            'v-neck': re.compile(r'브이넥|v-?neck|V넥', re.IGNORECASE),
            'henley': re.compile(r'헨리|henley', re.IGNORECASE),
        },
        'sleeve_length': {
            'short': re.compile(r'반팔|short sleeve|반소매', re.IGNORECASE),
            'long': re.compile(r'긴팔|long sleeve|장소매', re.IGNORECASE),
        },
        'pattern': {
            'solid': re.compile(r'무지|solid|단색', re.IGNORECASE),
            'stripe': re.compile(r'스트라이프|stripe|줄무늬', re.IGNORECASE),
            'graphic': re.compile(r'그래픽|graphic|프린트|print', re.IGNORECASE),
        },
        'length': {
            'short': re.compile(r'숏|short|짧은', re.IGNORECASE),
            'mid': re.compile(r'미디|mid|중간', re.IGNORECASE),
            'long': re.compile(r'롱|long|긴', re.IGNORECASE),
        },
        'closure': {
            'button': re.compile(r'버튼|button', re.IGNORECASE),
            'zip': re.compile(r'지퍼|zipper|zip|집업', re.IGNORECASE),
            'belt': re.compile(r'벨트|belt', re.IGNORECASE),
        },
        'lining': {
            'full': re.compile(r'전체.*안감|full lining|풀라이닝', re.IGNORECASE),
            'half': re.compile(r'부분.*안감|half lining|하프라이닝', re.IGNORECASE),
            'none': re.compile(r'안감.*없|no lining|언라인', re.IGNORECASE),
        },
    }
    
    @classmethod
    def extract(cls, text: str, category_slug: str) -> Dict[str, Any]:
        """텍스트에서 속성 추출
        
        Args:
            text: 상품 제목 + 설명
            category_slug: 카테고리 slug (down, slacks, jeans 등)
        
        Returns:
            추출된 속성 딕셔너리
        """
        attrs = {}
        
        # 카테고리별 속성 추출
        if category_slug == 'down':
            attrs.update(cls._extract_down_attributes(text))
        elif category_slug == 'slacks':
            attrs.update(cls._extract_slacks_attributes(text))
        elif category_slug == 'jeans':
            attrs.update(cls._extract_jeans_attributes(text))
        elif category_slug == 'crewneck':
            attrs.update(cls._extract_crewneck_attributes(text))
        elif category_slug == 'long-sleeve':
            attrs.update(cls._extract_longsleeve_attributes(text))
        elif category_slug == 'coat':
            attrs.update(cls._extract_coat_attributes(text))
        
        # 공통 속성 (fit, shell)
        if 'fit' not in attrs:
            attrs.update(cls._extract_common_fit(text))
        if 'shell' not in attrs:
            attrs.update(cls._extract_common_shell(text))
        
        return attrs
    
    @classmethod
    def _extract_down_attributes(cls, text: str) -> Dict[str, Any]:
        """다운 제품 속성 추출"""
        attrs = {}
        
        # Down Type
        for dtype, pattern in cls.PATTERNS['down_type'].items():
            if pattern.search(text):
                attrs['down_type'] = dtype
                break
        
        # Down Ratio
        for ratio, pattern in cls.PATTERNS['down_ratio'].items():
            if pattern.search(text):
                attrs['down_ratio'] = ratio
                break
        
        # Fill Power (숫자 추출)
        fp_match = cls.PATTERNS['fill_power'].search(text)
        if fp_match:
            attrs['fill_power'] = int(fp_match.group(1))
        
        # Hood
        for hood_val, pattern in cls.PATTERNS['hood'].items():
            if pattern.search(text):
                attrs['hood'] = hood_val
                break
        
        return attrs
    
    @classmethod
    def _extract_slacks_attributes(cls, text: str) -> Dict[str, Any]:
        """슬랙스 속성 추출"""
        attrs = {}
        
        # Waist Type
        for wtype, pattern in cls.PATTERNS['waist_type'].items():
            if pattern.search(text):
                attrs['waist_type'] = wtype
                break
        
        # Leg Opening
        for ltype, pattern in cls.PATTERNS['leg_opening'].items():
            if pattern.search(text):
                attrs['leg_opening'] = ltype
                break
        
        # Stretch
        if re.search(r'스트레치|stretch|신축|elastic', text, re.IGNORECASE):
            attrs['stretch'] = True
        
        # Pleats
        if re.search(r'더블.*플리츠|double.*pleat', text, re.IGNORECASE):
            attrs['pleats'] = 'double'
        elif re.search(r'싱글.*플리츠|single.*pleat', text, re.IGNORECASE):
            attrs['pleats'] = 'single'
        elif re.search(r'노플리츠|no.*pleat|플리츠.*없', text, re.IGNORECASE):
            attrs['pleats'] = 'none'
        
        return attrs
    
    @classmethod
    def _extract_jeans_attributes(cls, text: str) -> Dict[str, Any]:
        """청바지 속성 추출"""
        attrs = {}
        
        # Wash
        for wash_val, pattern in cls.PATTERNS['wash'].items():
            if pattern.search(text):
                attrs['wash'] = wash_val
                break
        
        # Cut
        for cut_val, pattern in cls.PATTERNS['cut'].items():
            if pattern.search(text):
                attrs['cut'] = cut_val
                break
        
        # Rise
        for rise_val, pattern in cls.PATTERNS['waist_type'].items():
            if pattern.search(text):
                attrs['rise'] = rise_val
                break
        
        # Stretch
        if re.search(r'스트레치|stretch|신축', text, re.IGNORECASE):
            attrs['stretch'] = True
        
        # Distressed
        if re.search(r'디스트레스|distressed|워싱|빈티지|vintage|찢어진', text, re.IGNORECASE):
            attrs['distressed'] = True
        
        return attrs
    
    @classmethod
    def _extract_crewneck_attributes(cls, text: str) -> Dict[str, Any]:
        """크루넥 속성 추출"""
        attrs = {}
        
        # Neckline
        for neck_val, pattern in cls.PATTERNS['neckline'].items():
            if pattern.search(text):
                attrs['neckline'] = neck_val
                break
        
        # Sleeve Length
        for sleeve_val, pattern in cls.PATTERNS['sleeve_length'].items():
            if pattern.search(text):
                attrs['sleeve_length'] = sleeve_val
                break
        
        # Pattern
        for pattern_val, pattern in cls.PATTERNS['pattern'].items():
            if pattern.search(text):
                attrs['pattern'] = pattern_val
                break
        
        return attrs
    
    @classmethod
    def _extract_longsleeve_attributes(cls, text: str) -> Dict[str, Any]:
        """긴팔 속성 추출"""
        attrs = {}
        
        # Neckline
        for neck_val, pattern in cls.PATTERNS['neckline'].items():
            if pattern.search(text):
                attrs['neckline'] = neck_val
                break
        
        # Sleeve Type
        if re.search(r'래글런|raglan', text, re.IGNORECASE):
            attrs['sleeve_type'] = 'raglan'
        elif re.search(r'세트인|set-?in', text, re.IGNORECASE):
            attrs['sleeve_type'] = 'set-in'
        
        # Layering
        if re.search(r'레이어링|layering|이너|inner', text, re.IGNORECASE):
            attrs['layering'] = True
        
        return attrs
    
    @classmethod
    def _extract_coat_attributes(cls, text: str) -> Dict[str, Any]:
        """코트 속성 추출"""
        attrs = {}
        
        # Length
        for length_val, pattern in cls.PATTERNS['length'].items():
            if pattern.search(text):
                attrs['length'] = length_val
                break
        
        # Closure
        for closure_val, pattern in cls.PATTERNS['closure'].items():
            if pattern.search(text):
                attrs['closure'] = closure_val
                break
        
        # Lining
        for lining_val, pattern in cls.PATTERNS['lining'].items():
            if pattern.search(text):
                attrs['lining'] = lining_val
                break
        
        # Hood
        for hood_val, pattern in cls.PATTERNS['hood'].items():
            if pattern.search(text):
                attrs['hood'] = hood_val
                break
        
        return attrs
    
    @classmethod
    def _extract_common_fit(cls, text: str) -> Dict[str, Any]:
        """공통 핏 추출"""
        for fit_val, pattern in cls.PATTERNS['fit'].items():
            if pattern.search(text):
                return {'fit': fit_val}
        return {}
    
    @classmethod
    def _extract_common_shell(cls, text: str) -> Dict[str, Any]:
        """공통 소재 추출"""
        for shell_val, pattern in cls.PATTERNS['shell'].items():
            if pattern.search(text):
                return {'shell': shell_val}
        return {}
