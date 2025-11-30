"""
Faiss Index Manager - 이미지 벡터 인덱스 관리
"""
import pickle
import logging
from pathlib import Path
from typing import List, Tuple, Dict, Optional, Any
from django.conf import settings

logger = logging.getLogger(__name__)

# Faiss 및 NumPy import 시도
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
    MISSING_PACKAGES = []
except ImportError as e:
    FAISS_AVAILABLE = False
    MISSING_PACKAGES = []
    
    try:
        import faiss
    except ImportError:
        MISSING_PACKAGES.append('faiss-cpu')
    
    try:
        import numpy as np
    except ImportError:
        MISSING_PACKAGES.append('numpy')
    
    logger.error(f"Faiss/NumPy not available. Missing: {', '.join(MISSING_PACKAGES)}")


class FaissIndexManager:
    """Faiss 벡터 인덱스 관리
    
    Features:
        - IndexFlatL2 (정확한 L2 거리)
        - 벡터 추가/삭제
        - K-NN 검색
        - 인덱스 저장/로드
        - Product ID 매핑
    """
    
    def __init__(self, dimension: int = 2048):
        """
        Args:
            dimension: 벡터 차원 (ResNet50 = 2048)
        """
        self.dimension = dimension
        self.product_ids: List[str] = []
        
        if not FAISS_AVAILABLE:
            self.index = None
            logger.warning(f"FaissIndexManager: Faiss not available. Missing: {', '.join(MISSING_PACKAGES)}")
        else:
            try:
                self.index = faiss.IndexFlatL2(dimension)
                logger.info(f"FaissIndexManager initialized (dim={dimension})")
            except Exception as e:
                self.index = None
                logger.error(f"Failed to initialize Faiss index: {str(e)}")
        
        # 인덱스 파일 경로
        self.index_dir = Path(settings.BASE_DIR) / 'data' / 'faiss'
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_path = self.index_dir / 'image_index.faiss'
        self.mapping_path = self.index_dir / 'product_mapping.pkl'
        
        # 기존 인덱스 자동 로드
        if self.index_path.exists() and self.mapping_path.exists():
            self.load()
    
    def add_vectors(self, vectors: np.ndarray, product_ids: List[str]) -> bool:
        """벡터 추가
        
        Args:
            vectors: [N, dimension] numpy array
            product_ids: 상품 ID 리스트 (길이 N)
        
        Returns:
            성공 여부
        """
        try:
            if len(vectors) != len(product_ids):
                logger.error("Vectors and product_ids length mismatch")
                return False
            
            # Float32 변환
            vectors = vectors.astype('float32')
            
            # 인덱스에 추가
            self.index.add(vectors)
            self.product_ids.extend(product_ids)
            
            logger.info(f"Added {len(vectors)} vectors to index (total: {self.index.ntotal})")
            return True
            
        except Exception as e:
            logger.error(f"Failed to add vectors: {str(e)}")
            return False
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 10,
        exclude_product_id: Optional[str] = None
    ) -> List[Dict[str, any]]:
        """유사 벡터 검색
        
        Args:
            query_vector: 쿼리 벡터 [dimension]
            k: 반환할 개수
            exclude_product_id: 제외할 상품 ID
        
        Returns:
            [{'product_id': str, 'distance': float, 'similarity': float}]
        """
        try:
            if self.index.ntotal == 0:
                logger.warning("Index is empty")
                return []
            
            # Float32 + 2D shape
            query_vector = query_vector.astype('float32').reshape(1, -1)
            
            # 검색 (k+1개 가져와서 자기 자신 제외)
            search_k = k + 10 if exclude_product_id else k
            distances, indices = self.index.search(query_vector, search_k)
            
            results = []
            for dist, idx in zip(distances[0], indices[0]):
                if idx == -1:  # 결과 없음
                    continue
                
                product_id = self.product_ids[idx]
                
                # 자기 자신 제외
                if exclude_product_id and product_id == exclude_product_id:
                    continue
                
                # L2 거리 -> 유사도 (0~1)
                # 거리가 작을수록 유사도 높음
                similarity = 1 / (1 + float(dist))
                
                results.append({
                    'product_id': product_id,
                    'distance': float(dist),
                    'similarity': similarity
                })
                
                if len(results) >= k:
                    break
            
            return results
            
        except Exception as e:
            logger.error(f"Search error: {str(e)}")
            return []
    
    def remove_by_product_id(self, product_id: str) -> bool:
        """상품 ID로 벡터 제거
        
        Note: Faiss IndexFlatL2는 직접 삭제 미지원
              -> 재구축 필요 (production에서는 IDMap 사용 권장)
        
        Args:
            product_id: 제거할 상품 ID
        
        Returns:
            성공 여부
        """
        try:
            if product_id not in self.product_ids:
                logger.warning(f"Product {product_id} not in index")
                return False
            
            # 현재 인덱스 재구축 (제외)
            indices_to_keep = [
                i for i, pid in enumerate(self.product_ids)
                if pid != product_id
            ]
            
            if not indices_to_keep:
                self.reset()
                return True
            
            # 기존 벡터 추출
            all_vectors = self.index.reconstruct_n(0, self.index.ntotal)
            keep_vectors = all_vectors[indices_to_keep]
            keep_ids = [self.product_ids[i] for i in indices_to_keep]
            
            # 재구축
            self.reset()
            self.add_vectors(keep_vectors, keep_ids)
            
            logger.info(f"Removed product {product_id} from index")
            return True
            
        except Exception as e:
            logger.error(f"Failed to remove product: {str(e)}")
            return False
    
    def save(self) -> bool:
        """인덱스 저장
        
        Returns:
            성공 여부
        """
        try:
            # Faiss 인덱스 저장
            faiss.write_index(self.index, str(self.index_path))
            
            # Product ID 매핑 저장
            with open(self.mapping_path, 'wb') as f:
                pickle.dump(self.product_ids, f)
            
            logger.info(f"Saved index with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to save index: {str(e)}")
            return False
    
    def load(self) -> bool:
        """인덱스 로드
        
        Returns:
            성공 여부
        """
        try:
            if not self.index_path.exists():
                logger.warning("Index file not found")
                return False
            
            # Faiss 인덱스 로드
            self.index = faiss.read_index(str(self.index_path))
            
            # Product ID 매핑 로드
            with open(self.mapping_path, 'rb') as f:
                self.product_ids = pickle.load(f)
            
            logger.info(f"Loaded index with {self.index.ntotal} vectors")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load index: {str(e)}")
            return False
    
    def reset(self):
        """인덱스 초기화"""
        self.index = faiss.IndexFlatL2(self.dimension)
        self.product_ids = []
        logger.info("Index reset")
    
    def get_stats(self) -> Dict[str, any]:
        """인덱스 통계
        
        Returns:
            통계 딕셔너리
        """
        return {
            'total_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'product_count': len(self.product_ids),
            'index_type': 'IndexFlatL2',
            'index_file_exists': self.index_path.exists(),
            'mapping_file_exists': self.mapping_path.exists()
        }
