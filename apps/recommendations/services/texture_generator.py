"""
Texture Generator Service - Hugging Face Inference Providers 기반 질감 이미지 생성
"""
import os
import logging
from typing import Optional, Dict, Any
from PIL import Image
from io import BytesIO
import base64

logger = logging.getLogger(__name__)


class TextureGeneratorService:
    """질감 이미지 생성 서비스
    
    Features:
        - Hugging Face Inference Providers API 활용
        - 프롬프트 기반 질감 이미지 생성
        - FLUX.1-dev 모델 사용 (고품질 photorealistic 이미지)
    
    Usage:
        generator = TextureGeneratorService()
        image = generator.generate_texture(
            material='cotton',
            color='navy blue',
            product_type='jacket'
        )
    """
    
    # Hugging Face Inference Providers - Text-to-Image
    # FLUX.1-dev: 최신 고품질 이미지 생성 모델
    DEFAULT_MODEL = "black-forest-labs/FLUX.1-dev"
    
    def __init__(self, api_token: Optional[str] = None):
        """
        Args:
            api_token: Hugging Face API token (없으면 환경변수에서 읽음)
        """
        self.api_token = api_token or os.getenv('HUGGING_FACE_API_TOKEN')
        
        if not self.api_token:
            raise ValueError(
                "Hugging Face API token is required for texture generation. "
                "Please set HUGGING_FACE_API_TOKEN environment variable or pass api_token parameter."
            )
        
        logger.info(f"TextureGeneratorService initialized with {self.DEFAULT_MODEL} model")
    
    def generate_texture(
        self,
        material: str,
        color: Optional[str] = None,
        product_type: Optional[str] = None,
        quality: str = 'high',
        reference_image_url: Optional[str] = None
    ) -> Optional[Image.Image]:
        """질감 이미지 생성 - 실제 상품의 질감을 확대하여 상세하게 표현
        
        Args:
            material: 소재 구성 (e.g., 'cotton 95%, elastane 5%')
            color: 색상 (e.g., 'navy blue', 'black', 'beige')
            product_type: 상품 타입 (e.g., 'jacket', 'pants')
            quality: 품질 ('high', 'medium', 'low')
            reference_image_url: 참조할 상품 이미지 URL (질감 분석용)
        
        Returns:
            PIL Image 또는 None
        """
        # 프롬프트 구성 (소재 구성 정보와 참조 이미지 활용)
        prompt = self._build_detailed_texture_prompt(
            material, color, product_type, quality, reference_image_url
        )
        
        logger.info(f"Generating detailed texture with {self.DEFAULT_MODEL}: {prompt[:100]}...")
        
        # Hugging Face Inference Providers로 생성
        image = self._generate_via_huggingface(prompt)
        
        if image is None:
            raise RuntimeError(
                f"Failed to generate texture via Hugging Face Inference Providers. "
                f"Please check API status and try again."
            )
        
        return image
    
    def _build_detailed_texture_prompt(
        self,
        material_composition: str,
        color: Optional[str],
        product_type: Optional[str],
        quality: str,
        reference_image_url: Optional[str] = None
    ) -> str:
        """상세 질감 프롬프트 생성 - 실제 소재 구성을 반영하여 확대된 질감 표현
        
        Args:
            material_composition: 소재 구성 문자열 (e.g., "cotton 95%, elastane 5%")
            color: 색상
            product_type: 상품 타입
            quality: 품질 레벨
            reference_image_url: 참조 이미지 URL (현재는 분석용, 향후 img2img 가능)
        
        Returns:
            FLUX.1-dev 최적화 프롬프트
        """
        # 소재 구성 파싱
        materials = self._parse_material_composition(material_composition)
        
        # 기본 프롬프트: 극도로 확대된 질감
        parts = [
            "ultra high resolution macro photograph",
            "extreme close-up of fabric texture",
            "magnified textile surface"
        ]
        
        # 색상
        if color:
            parts.append(f"{color} colored")
        
        # 주요 소재 기반 질감 디테일
        main_material = materials[0] if materials else 'fabric'
        material_details = self._get_material_texture_details(main_material)
        parts.extend(material_details)
        
        # 소재 블렌드 특성 (혼방 소재인 경우)
        if len(materials) > 1:
            blend_description = self._describe_material_blend(materials)
            if blend_description:
                parts.append(blend_description)
        
        # 상품 타입별 질감 특성
        if product_type:
            type_specific = self._get_product_type_texture(product_type, main_material)
            if type_specific:
                parts.append(type_specific)
        
        # 품질 설정 - 극도로 상세한 질감 표현
        quality_settings = {
            'high': (
                'photorealistic 16k resolution, professional textile microscopy, '
                'studio lighting, ultra sharp focus, individual fiber strands visible, '
                'weave pattern details, textile grain structure, macro lens photography, '
                'fabric thread count visible'
            ),
            'medium': (
                'photorealistic 8k resolution, detailed fabric weave pattern, '
                'clear fiber texture, professional lighting, sharp macro focus'
            ),
            'low': (
                'realistic fabric close-up, visible weave pattern, natural texture detail'
            )
        }
        parts.append(quality_settings.get(quality, quality_settings['high']))
        
        # Negative elements
        parts.append("no people, no faces, no objects, no logos, only fabric texture surface")
        
        prompt = ', '.join(parts)
        
        logger.info(f"Generated detailed texture prompt for: {material_composition}")
        
        return prompt
    
    def _parse_material_composition(self, composition: str) -> list:
        """소재 구성 문자열 파싱
        
        Args:
            composition: "cotton 95%, elastane 5%" 형식
        
        Returns:
            소재 리스트 (비율 순) ['cotton', 'elastane']
        """
        if not composition:
            return ['cotton']  # 기본값
        
        # 쉼표로 분리하고 소재명만 추출
        materials = []
        for part in composition.split(','):
            part = part.strip().lower()
            # 퍼센트 제거하고 소재명만
            material_name = part.split('%')[0].strip()
            # 숫자 제거
            material_name = ''.join([c for c in material_name if not c.isdigit()]).strip()
            if material_name:
                materials.append(material_name)
        
        return materials if materials else ['cotton']
    
    def _get_material_texture_details(self, material: str) -> list:
        """소재별 상세 질감 표현
        
        Args:
            material: 소재명
        
        Returns:
            질감 디테일 설명 리스트
        """
        texture_library = {
            'cotton': [
                'natural cotton fiber weave',
                'soft breathable textile structure',
                'visible cotton thread texture',
                'natural fiber grain pattern'
            ],
            'polyester': [
                'synthetic polyester fiber weave',
                'smooth uniform textile surface',
                'consistent thread pattern',
                'durable synthetic texture'
            ],
            'wool': [
                'natural wool fiber texture',
                'warm fuzzy textile surface',
                'irregular wool thread pattern',
                'soft organic fiber structure'
            ],
            'nylon': [
                'smooth nylon weave pattern',
                'water-resistant textile surface',
                'technical fabric structure',
                'uniform synthetic fiber texture'
            ],
            'elastane': [
                'elastic fiber integration',
                'stretchy textile structure',
                'flexible fabric weave'
            ],
            'spandex': [
                'elastic spandex fiber blend',
                'stretchy fabric texture',
                'flexible weave pattern'
            ],
            'acrylic': [
                'soft acrylic fiber texture',
                'wool-like synthetic weave',
                'warm fabric structure'
            ],
            'rayon': [
                'smooth rayon fiber texture',
                'silk-like synthetic weave',
                'lustrous fabric surface'
            ],
            'cashmere': [
                'luxurious cashmere fiber',
                'ultra soft premium texture',
                'fine wool fiber structure',
                'delicate natural weave'
            ],
            'leather': [
                'genuine leather grain pattern',
                'natural hide texture',
                'organic surface irregularities',
                'premium leather detail'
            ],
            'denim': [
                'cotton denim twill weave',
                'diagonal ribbed pattern',
                'heavy duty textile structure',
                'selvage edge detail'
            ]
        }
        
        # 기본 fabric 처리
        return texture_library.get(material, [
            f'{material} fabric texture',
            'woven textile surface',
            'detailed fiber pattern'
        ])
    
    def _describe_material_blend(self, materials: list) -> Optional[str]:
        """혼방 소재의 특성 설명
        
        Args:
            materials: 소재 리스트
        
        Returns:
            블렌드 특성 설명
        """
        blend_descriptions = {
            ('cotton', 'elastane'): 'cotton-elastane blend with stretch fibers',
            ('cotton', 'spandex'): 'cotton-spandex blend with elastic properties',
            ('cotton', 'polyester'): 'cotton-polyester blend with durability',
            ('wool', 'polyester'): 'wool-polyester blend with warmth and strength',
            ('wool', 'cashmere'): 'premium wool-cashmere blend with luxury softness',
            ('polyester', 'rayon'): 'polyester-rayon blend with smooth drape',
        }
        
        if len(materials) >= 2:
            key = tuple(sorted(materials[:2]))
            return blend_descriptions.get(key, f'blended {materials[0]}-{materials[1]} textile')
        
        return None
    
    def _get_product_type_texture(self, product_type: str, material: str) -> Optional[str]:
        """상품 타입에 따른 질감 특성
        
        Args:
            product_type: 상품 타입
            material: 주요 소재
        
        Returns:
            타입별 질감 설명
        """
        type_textures = {
            'down': 'quilted padding pattern with insulation texture',
            'coat': 'heavy duty outer garment weave with dense structure',
            'jacket': 'durable outer layer textile with protective finish',
            'jeans': 'heavy weight denim with diagonal twill weave',
            'slacks': 'formal dress fabric with smooth refined texture',
            'crew': 'comfortable knit textile with soft hand feel',
            'crewneck': 'knit sweater texture with loop structure',
            'long': 'lightweight jersey knit with soft drape',
            'shirt': 'breathable woven fabric with crisp texture',
        }
        
        # product_type이 포함된 키 찾기
        for key, description in type_textures.items():
            if key in product_type.lower():
                return description
        
        return None
    
    def _build_prompt(
        self,
        material: str,
        color: Optional[str],
        product_type: Optional[str],
        quality: str
    ) -> str:
        """프롬프트 생성 - FLUX.1-dev에 최적화된 의류 질감 프롬프트
        
        Returns:
            Text-to-image 프롬프트 문자열
        """
        # 소재별 세부 질감 키워드
        material_specifics = {
            'cotton': 'soft cotton weave, natural fiber texture, breathable fabric',
            'wool': 'fine wool knit, warm textile, natural fiber pattern',
            'denim': 'cotton denim weave, selvage edge, diagonal twill pattern',
            'leather': 'genuine leather grain, natural hide texture, premium quality',
            'polyester': 'synthetic fiber weave, smooth textile surface',
            'nylon': 'water-resistant nylon, quilted pattern, technical fabric',
            'silk': 'luxurious silk fabric, smooth sheen, delicate weave',
            'linen': 'natural linen weave, breathable texture, crisp fabric',
        }
        
        # 기본 프롬프트: 극도로 사실적인 근접 촬영
        parts = ["extreme macro close-up photograph of"]
        
        # 색상
        if color:
            parts.append(color)
        
        # 소재 + 세부 키워드
        material_lower = material.lower()
        if material_lower in material_specifics:
            parts.append(material_specifics[material_lower])
        else:
            parts.append(f"{material} fabric texture")
        
        # 상품 타입별 추가 컨텍스트
        if product_type:
            product_context = {
                'jacket': 'outer garment material',
                'pants': 'durable clothing fabric',
                'coat': 'premium outerwear textile',
                'shirt': 'comfortable clothing material',
            }
            if product_type.lower() in product_context:
                parts.append(product_context[product_type.lower()])
        
        # 품질 설정 - FLUX.1-dev에 최적화
        quality_settings = {
            'high': 'photorealistic, 8k resolution, professional textile photography, studio lighting, sharp focus, highly detailed weave pattern, macro lens',
            'medium': 'photorealistic, detailed fabric texture, natural lighting, clear focus',
            'low': 'realistic fabric close-up, natural texture'
        }
        parts.append(quality_settings.get(quality, quality_settings['medium']))
        
        # FLUX는 negative prompt를 별도로 지원하지 않으므로 프롬프트에 포함
        parts.append("no people, no faces, no objects, only fabric texture")
        
        prompt = ', '.join(parts)
        
        return prompt
    
    def _generate_via_huggingface(self, prompt: str) -> Optional[Image.Image]:
        """Hugging Face Inference Providers를 통한 이미지 생성
        
        Args:
            prompt: 생성 프롬프트
        
        Returns:
            PIL Image 또는 None
        """
        try:
            from huggingface_hub import InferenceClient
            
            # InferenceClient 초기화
            client = InferenceClient(api_key=self.api_token)
            
            logger.info(f"Calling Hugging Face Inference Providers: {self.DEFAULT_MODEL}")
            logger.info(f"Prompt: {prompt[:150]}...")
            
            # Text-to-Image 생성
            image = client.text_to_image(
                prompt=prompt,
                model=self.DEFAULT_MODEL
            )
            
            if image:
                logger.info(f"Successfully generated texture: {image.size}")
                return image
            else:
                logger.error("Generated image is None")
                return None
                
        except ImportError:
            logger.error("huggingface_hub library not installed. Install with: pip install huggingface_hub")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in texture generation: {str(e)}", exc_info=True)
            return None
    
    def save_texture(
        self,
        image: Image.Image,
        product_id: str,
        output_dir: str = 'media/textures'
    ) -> str:
        """생성된 질감 이미지 저장
        
        Args:
            image: PIL Image
            product_id: 상품 ID
            output_dir: 저장 디렉토리
        
        Returns:
            저장된 파일 경로
        """
        import os
        from django.conf import settings
        
        # 디렉토리 생성
        full_dir = os.path.join(settings.BASE_DIR, output_dir)
        os.makedirs(full_dir, exist_ok=True)
        
        # 파일명 생성
        filename = f"{product_id}_texture.jpg"
        filepath = os.path.join(full_dir, filename)
        
        # 저장
        image.save(filepath, 'JPEG', quality=90)
        
        logger.info(f"Texture saved to {filepath}")
        return filepath
    
    def image_to_base64(self, image: Image.Image) -> str:
        """이미지를 Base64 문자열로 변환
        
        Args:
            image: PIL Image
        
        Returns:
            Base64 인코딩 문자열
        """
        buffer = BytesIO()
        image.save(buffer, format='JPEG')
        img_bytes = buffer.getvalue()
        img_base64 = base64.b64encode(img_bytes).decode('utf-8')
        
        return f"data:image/jpeg;base64,{img_base64}"
