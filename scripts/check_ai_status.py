"""AI 패키지 상태 확인 스크립트"""
import os
import sys

# Django 프로젝트 루트를 경로에 추가
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

# Django 설정
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

import django
django.setup()

print("=" * 60)
print("AI 패키지 상태 확인")
print("=" * 60)

# 1. ImageEmbedding 서비스 확인
print("\n[1] ImageEmbedding Service")
try:
    from apps.recommendations.services.image_embedding import AI_AVAILABLE, MISSING_PACKAGES
    print(f"   ✅ AI Available: {AI_AVAILABLE}")
    if MISSING_PACKAGES:
        print(f"   ❌ Missing Packages: {', '.join(MISSING_PACKAGES)}")
    else:
        print(f"   ✅ All packages installed")
        
        # 서비스 초기화 테스트
        from apps.recommendations.services.image_embedding import ImageEmbeddingService
        service = ImageEmbeddingService()
        if service.model is not None:
            print(f"   ✅ ResNet50 model loaded successfully")
        else:
            print(f"   ❌ Model initialization failed")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 2. Faiss Index Manager 확인
print("\n[2] Faiss Index Manager")
try:
    from apps.recommendations.services.faiss_manager import FAISS_AVAILABLE, MISSING_PACKAGES as FAISS_MISSING
    print(f"   ✅ Faiss Available: {FAISS_AVAILABLE}")
    if FAISS_MISSING:
        print(f"   ❌ Missing Packages: {', '.join(FAISS_MISSING)}")
    else:
        print(f"   ✅ All packages installed")
        
        # 인덱스 매니저 초기화 테스트
        from apps.recommendations.services.faiss_manager import FaissIndexManager
        manager = FaissIndexManager()
        if manager.index is not None:
            print(f"   ✅ Faiss index initialized (ntotal: {manager.index.ntotal})")
        else:
            print(f"   ❌ Index initialization failed")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 3. Texture Generator 확인
print("\n[3] Texture Generator Service")
try:
    from apps.recommendations.services.texture_generator import TextureGeneratorService
    try:
        generator = TextureGeneratorService()
        print(f"   ✅ Realistic Vision v6.0 model configured")
        print(f"   ✅ Hugging Face API token set")
    except ValueError as ve:
        print(f"   ⚠️  API Token not set: {str(ve)}")
        print(f"   💡 Set HUGGING_FACE_API_TOKEN environment variable for texture generation")
except Exception as e:
    print(f"   ❌ Error: {str(e)}")

# 4. 패키지 버전 확인
print("\n[4] Installed Package Versions")
try:
    import torch
    import torchvision
    import faiss
    import numpy as np
    print(f"   torch: {torch.__version__}")
    print(f"   torchvision: {torchvision.__version__}")
    print(f"   numpy: {np.__version__}")
    print(f"   faiss-cpu: installed")
except ImportError as e:
    print(f"   ❌ Import error: {str(e)}")

print("\n" + "=" * 60)
print("✅ AI 시스템 진단 완료")
print("=" * 60)
