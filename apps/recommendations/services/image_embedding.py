"""
Image Embedding Service - ResNet50 기반 이미지 벡터화
"""
import logging
from typing import Optional, List
from io import BytesIO
from django.core.cache import cache

logger = logging.getLogger(__name__)

# AI 패키지 import 시도
try:
    import torch
    import torchvision.transforms as transforms
    from torchvision.models import resnet50, ResNet50_Weights
    from PIL import Image
    import numpy as np
    import requests
    AI_AVAILABLE = True
    MISSING_PACKAGES = []
except ImportError as e:
    AI_AVAILABLE = False
    MISSING_PACKAGES = []
    
    # 누락된 패키지 확인
    try:
        import torch
    except ImportError:
        MISSING_PACKAGES.append('torch')
    
    try:
        import torchvision
    except ImportError:
        MISSING_PACKAGES.append('torchvision')
    
    try:
        import numpy
    except ImportError:
        MISSING_PACKAGES.append('numpy')
    
    try:
        from PIL import Image
    except ImportError:
        MISSING_PACKAGES.append('Pillow')
    
    try:
        import requests
    except ImportError:
        MISSING_PACKAGES.append('requests')
    
    logger.error(f"AI packages not available. Missing: {', '.join(MISSING_PACKAGES)}")


class ImageEmbeddingService:
    """ResNet50 기반 이미지 임베딩 생성
    
    Features:
        - ResNet50 pre-trained model
        - 512차원 벡터 추출 (fc layer 이전)
        - URL에서 이미지 다운로드
        - 배치 처리 지원
        - 캐싱 전략
    """
    
    def __init__(self):
        """모델 초기화"""
        if not AI_AVAILABLE:
            self.model = None
            self.transform = None
            self.device = None
            logger.warning(f"ImageEmbeddingService: AI packages not installed. Missing: {', '.join(MISSING_PACKAGES)}")
            return
        
        try:
            self.device = torch.device('cpu')  # CPU 전용
            
            # ResNet50 로드 (ImageNet pre-trained)
            weights = ResNet50_Weights.DEFAULT
            self.model = resnet50(weights=weights)
            
            # FC layer 제거 (2048차원 feature 추출)
            self.model = torch.nn.Sequential(*list(self.model.children())[:-1])
            self.model.eval()
            self.model.to(self.device)
            
            # 이미지 전처리 (ImageNet 표준)
            self.transform = weights.transforms()
            
            logger.info("ImageEmbeddingService initialized (CPU mode)")
        except Exception as e:
            self.model = None
            self.transform = None
            self.device = None
            logger.error(f"Failed to initialize ImageEmbeddingService: {str(e)}")
    
    def download_image(self, url: str, timeout: int = 10) -> Optional['Image.Image']:
        """URL에서 이미지 다운로드
        
        Args:
            url: 이미지 URL
            timeout: 타임아웃 (초)
        
        Returns:
            PIL Image 또는 None
        """
        if not AI_AVAILABLE:
            logger.error(f"Cannot download image: Missing packages {MISSING_PACKAGES}")
            return None
        
        try:
            response = requests.get(url, timeout=timeout)
            response.raise_for_status()
            
            img = Image.open(BytesIO(response.content))
            
            # RGB로 변환 (RGBA, Grayscale 등 처리)
            if img.mode != 'RGB':
                img = img.convert('RGB')
            
            return img
            
        except Exception as e:
            logger.error(f"Failed to download image from {url}: {str(e)}")
            return None
    
    def preprocess_image(self, image: Image.Image) -> torch.Tensor:
        """이미지 전처리
        
        Args:
            image: PIL Image
        
        Returns:
            Preprocessed tensor [1, 3, 224, 224]
        """
        # Resize + Normalize
        img_tensor = self.transform(image)
        
        # Batch dimension 추가
        img_tensor = img_tensor.unsqueeze(0)
        
        return img_tensor.to(self.device)
    
    def extract_features(self, image: 'Image.Image') -> Optional['np.ndarray']:
        """이미지에서 feature vector 추출
        
        Args:
            image: PIL Image
        
        Returns:
            2048차원 numpy array 또는 None
        """
        if not AI_AVAILABLE or self.model is None:
            logger.error(f"Cannot extract features: AI packages not available. Missing: {MISSING_PACKAGES}")
            return None
        
        try:
            # 전처리
            img_tensor = self.preprocess_image(image)
            
            # Feature 추출 (no gradient)
            with torch.no_grad():
                features = self.model(img_tensor)
            
            # [1, 2048, 1, 1] -> [2048]
            features = features.squeeze().cpu().numpy()
            
            # L2 normalize (코사인 유사도 최적화)
            features = features / np.linalg.norm(features)
            
            return features.astype('float32')
            
        except Exception as e:
            logger.error(f"Failed to extract features: {str(e)}")
            return None
    
    def get_embedding_from_url(self, url: str, use_cache: bool = True) -> Optional[np.ndarray]:
        """URL에서 이미지 임베딩 생성
        
        Args:
            url: 이미지 URL
            use_cache: 캐시 사용 여부
        
        Returns:
            2048차원 embedding 또는 None
        """
        # 캐시 확인
        cache_key = f'img_emb:{url}'
        if use_cache:
            try:
                cached = cache.get(cache_key)
                if cached is not None:
                    return np.frombuffer(cached, dtype='float32')
            except Exception as e:
                logger.warning(f"Cache get failed: {str(e)}, continuing without cache")
        
        # 이미지 다운로드
        image = self.download_image(url)
        if image is None:
            return None
        
        # Feature 추출
        embedding = self.extract_features(image)
        
        # 캐시 저장 (1시간)
        if embedding is not None and use_cache:
            try:
                cache.set(cache_key, embedding.tobytes(), timeout=3600)
            except Exception as e:
                logger.warning(f"Cache set failed: {str(e)}, continuing without cache")
        
        return embedding
    
    def batch_extract_features(
        self,
        images: List[Image.Image],
        batch_size: int = 32
    ) -> List[Optional[np.ndarray]]:
        """배치 이미지 feature 추출
        
        Args:
            images: PIL Image 리스트
            batch_size: 배치 크기
        
        Returns:
            Embedding 리스트
        """
        embeddings = []
        
        for i in range(0, len(images), batch_size):
            batch = images[i:i + batch_size]
            batch_tensors = []
            
            # 전처리
            for img in batch:
                try:
                    tensor = self.preprocess_image(img)
                    batch_tensors.append(tensor)
                except Exception as e:
                    logger.error(f"Preprocess error in batch: {str(e)}")
                    batch_tensors.append(None)
            
            # 유효한 tensor만 배치 처리
            valid_indices = [idx for idx, t in enumerate(batch_tensors) if t is not None]
            if not valid_indices:
                embeddings.extend([None] * len(batch))
                continue
            
            valid_tensors = torch.cat([batch_tensors[idx] for idx in valid_indices], dim=0)
            
            # Feature 추출
            with torch.no_grad():
                features = self.model(valid_tensors)
            
            # [N, 2048, 1, 1] -> [N, 2048]
            features = features.squeeze().cpu().numpy()
            
            # L2 normalize
            if len(features.shape) == 1:  # 단일 이미지
                features = features / np.linalg.norm(features)
                features = features.reshape(1, -1)
            else:
                norms = np.linalg.norm(features, axis=1, keepdims=True)
                features = features / norms
            
            # 결과 매핑
            result_idx = 0
            for idx in range(len(batch)):
                if idx in valid_indices:
                    embeddings.append(features[result_idx].astype('float32'))
                    result_idx += 1
                else:
                    embeddings.append(None)
        
        return embeddings
    
    def compute_similarity(
        self,
        embedding1: np.ndarray,
        embedding2: np.ndarray
    ) -> float:
        """두 임베딩 간 코사인 유사도 계산
        
        Args:
            embedding1: 첫 번째 임베딩
            embedding2: 두 번째 임베딩
        
        Returns:
            코사인 유사도 (0.0 ~ 1.0)
        """
        # L2 normalized vectors의 dot product = cosine similarity
        similarity = np.dot(embedding1, embedding2)
        
        # -1~1 범위를 0~1로 변환
        return float((similarity + 1) / 2)
