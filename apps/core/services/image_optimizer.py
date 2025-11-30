"""
이미지 최적화 유틸리티
"""
import os
from PIL import Image
from io import BytesIO
from typing import Tuple, Optional


class ImageOptimizer:
    """이미지 최적화 서비스
    
    Features:
        - WebP 변환
        - 리사이징
        - 품질 최적화
        - Thumbnail 생성
    """
    
    def __init__(self):
        self.webp_quality = 80
        self.jpeg_quality = 85
        self.max_width = 1200
        self.max_height = 1200
    
    def convert_to_webp(
        self,
        image_path: str,
        output_path: Optional[str] = None,
        quality: int = 80
    ) -> str:
        """이미지를 WebP 포맷으로 변환
        
        Args:
            image_path: 원본 이미지 경로
            output_path: 출력 경로 (None이면 자동 생성)
            quality: WebP 품질 (1-100)
        
        Returns:
            변환된 WebP 이미지 경로
        """
        if not output_path:
            base, _ = os.path.splitext(image_path)
            output_path = f"{base}.webp"
        
        try:
            with Image.open(image_path) as img:
                # RGBA -> RGB 변환 (WebP는 투명도 지원하지만 최적화)
                if img.mode in ('RGBA', 'LA'):
                    background = Image.new('RGB', img.size, (255, 255, 255))
                    background.paste(img, mask=img.split()[-1])
                    img = background
                
                # WebP로 저장
                img.save(output_path, 'WEBP', quality=quality, method=6)
            
            return output_path
        except Exception as e:
            raise Exception(f"WebP 변환 실패: {str(e)}")
    
    def resize_image(
        self,
        image_path: str,
        max_width: int = 1200,
        max_height: int = 1200,
        output_path: Optional[str] = None
    ) -> str:
        """이미지 리사이징 (비율 유지)
        
        Args:
            image_path: 원본 이미지 경로
            max_width: 최대 너비
            max_height: 최대 높이
            output_path: 출력 경로
        
        Returns:
            리사이징된 이미지 경로
        """
        if not output_path:
            output_path = image_path
        
        try:
            with Image.open(image_path) as img:
                # 비율 유지하며 리사이징
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # 저장
                img.save(output_path, optimize=True, quality=self.jpeg_quality)
            
            return output_path
        except Exception as e:
            raise Exception(f"리사이징 실패: {str(e)}")
    
    def create_thumbnail(
        self,
        image_path: str,
        size: Tuple[int, int] = (300, 300),
        output_path: Optional[str] = None
    ) -> str:
        """썸네일 생성
        
        Args:
            image_path: 원본 이미지 경로
            size: 썸네일 크기 (width, height)
            output_path: 출력 경로
        
        Returns:
            썸네일 이미지 경로
        """
        if not output_path:
            base, ext = os.path.splitext(image_path)
            output_path = f"{base}_thumb{ext}"
        
        try:
            with Image.open(image_path) as img:
                # 중앙 크롭 후 리사이징
                img_ratio = img.width / img.height
                target_ratio = size[0] / size[1]
                
                if img_ratio > target_ratio:
                    # 이미지가 더 넓음 - 좌우 크롭
                    new_width = int(img.height * target_ratio)
                    left = (img.width - new_width) // 2
                    img = img.crop((left, 0, left + new_width, img.height))
                else:
                    # 이미지가 더 높음 - 상하 크롭
                    new_height = int(img.width / target_ratio)
                    top = (img.height - new_height) // 2
                    img = img.crop((0, top, img.width, top + new_height))
                
                # 리사이징
                img = img.resize(size, Image.Resampling.LANCZOS)
                
                # 저장
                img.save(output_path, optimize=True, quality=self.jpeg_quality)
            
            return output_path
        except Exception as e:
            raise Exception(f"썸네일 생성 실패: {str(e)}")
    
    def optimize_for_web(
        self,
        image_path: str,
        output_dir: Optional[str] = None
    ) -> dict:
        """웹 최적화 (여러 크기 생성)
        
        Args:
            image_path: 원본 이미지 경로
            output_dir: 출력 디렉토리
        
        Returns:
            생성된 이미지 경로들
        """
        if not output_dir:
            output_dir = os.path.dirname(image_path)
        
        base_name = os.path.splitext(os.path.basename(image_path))[0]
        
        results = {}
        
        try:
            # 원본 크기 WebP
            webp_path = os.path.join(output_dir, f"{base_name}.webp")
            results['webp_original'] = self.convert_to_webp(image_path, webp_path)
            
            # 썸네일 (300x300)
            thumb_path = os.path.join(output_dir, f"{base_name}_thumb.jpg")
            results['thumbnail'] = self.create_thumbnail(image_path, (300, 300), thumb_path)
            
            # 중간 크기 (800x800)
            medium_path = os.path.join(output_dir, f"{base_name}_medium.jpg")
            results['medium'] = self.resize_image(image_path, 800, 800, medium_path)
            
            # WebP 썸네일
            webp_thumb_path = os.path.join(output_dir, f"{base_name}_thumb.webp")
            results['webp_thumbnail'] = self.convert_to_webp(thumb_path, webp_thumb_path)
            
            return results
        except Exception as e:
            raise Exception(f"웹 최적화 실패: {str(e)}")
    
    def get_image_info(self, image_path: str) -> dict:
        """이미지 정보 조회
        
        Args:
            image_path: 이미지 경로
        
        Returns:
            이미지 정보 (width, height, format, size)
        """
        try:
            with Image.open(image_path) as img:
                return {
                    'width': img.width,
                    'height': img.height,
                    'format': img.format,
                    'mode': img.mode,
                    'size_bytes': os.path.getsize(image_path),
                    'size_kb': round(os.path.getsize(image_path) / 1024, 2)
                }
        except Exception as e:
            raise Exception(f"이미지 정보 조회 실패: {str(e)}")


def generate_og_image_url(product) -> str:
    """OG 이미지 URL 생성 (상품용)
    
    Args:
        product: Product 모델 인스턴스
    
    Returns:
        OG 이미지 URL
    """
    if hasattr(product, 'image_url') and product.image_url:
        # WebP가 있으면 WebP 사용, 없으면 원본
        image_url = product.image_url
        
        # WebP 변환 URL 생성
        if not image_url.endswith('.webp'):
            base_url = image_url.rsplit('.', 1)[0]
            webp_url = f"{base_url}.webp"
            return webp_url
        
        return image_url
    
    # 기본 OG 이미지
    return "/static/images/og-default.jpg"


def generate_srcset(base_url: str, sizes: list = None) -> str:
    """반응형 이미지 srcset 생성
    
    Args:
        base_url: 기본 이미지 URL
        sizes: 크기 리스트 (예: [300, 600, 1200])
    
    Returns:
        srcset 문자열
    """
    if sizes is None:
        sizes = [300, 600, 900, 1200]
    
    base_name, ext = base_url.rsplit('.', 1)
    
    srcset_parts = []
    for size in sizes:
        srcset_parts.append(f"{base_name}_{size}w.{ext} {size}w")
    
    return ', '.join(srcset_parts)
