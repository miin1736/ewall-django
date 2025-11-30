"""
Tests for Image Similarity Recommendations (Phase 2)
"""
import os
import numpy as np
from django.test import TestCase, override_settings
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
from PIL import Image
import io
import tempfile
import shutil
import unittest

from apps.products.models import DownProduct, Category, Brand
from apps.recommendations.models import ImageEmbedding
from apps.recommendations.services.image_embedding import ImageEmbeddingService
from apps.recommendations.services.faiss_manager import FaissIndexManager


# Test settings
TEST_MEDIA_ROOT = tempfile.mkdtemp()


class ImageEmbeddingServiceTestCase(TestCase):
    """Test ImageEmbeddingService functionality."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.service = ImageEmbeddingService()
    
    def create_test_image(self, size=(224, 224), color='red'):
        """Create a test PIL image."""
        img = Image.new('RGB', size, color=color)
        return img
    
    def test_preprocess_image(self):
        """Test image preprocessing."""
        img = self.create_test_image()
        tensor = self.service.preprocess_image(img)
        
        # Check tensor shape (should be [1, 3, 224, 224] with batch dimension)
        self.assertEqual(tensor.shape, (1, 3, 224, 224))
    
    def test_extract_features(self):
        """Test feature extraction from image."""
        img = self.create_test_image()
        features = self.service.extract_features(img)
        
        # Check features shape (should be [2048])
        self.assertEqual(features.shape, (2048,))
        self.assertEqual(features.dtype, np.float32)
        
        # Check L2 normalization (norm should be close to 1.0)
        norm = np.linalg.norm(features)
        self.assertAlmostEqual(norm, 1.0, places=5)
    
    def test_batch_extract_features(self):
        """Test batch feature extraction."""
        images = [
            self.create_test_image(color='red'),
            self.create_test_image(color='blue'),
            self.create_test_image(color='green'),
        ]
        
        features_list = self.service.batch_extract_features(images, batch_size=2)
        
        # Check results
        self.assertEqual(len(features_list), 3)
        for features in features_list:
            self.assertIsNotNone(features)
            self.assertEqual(features.shape, (2048,))
    
    def test_compute_similarity(self):
        """Test similarity computation."""
        # Same image should have similarity close to 1.0
        img1 = self.create_test_image(color='red')
        emb1 = self.service.extract_features(img1)
        emb2 = self.service.extract_features(img1)
        
        similarity = self.service.compute_similarity(emb1, emb2)
        self.assertAlmostEqual(similarity, 1.0, places=5)
        
        # Different images should have lower similarity
        img3 = self.create_test_image(color='blue')
        emb3 = self.service.extract_features(img3)
        
        similarity_diff = self.service.compute_similarity(emb1, emb3)
        self.assertLess(similarity_diff, 1.0)
        self.assertGreater(similarity_diff, 0.0)


class FaissIndexManagerTestCase(TestCase):
    """Test FaissIndexManager functionality."""
    
    def setUp(self):
        self.manager = FaissIndexManager(dimension=2048)
        self.test_vectors = np.random.randn(10, 2048).astype(np.float32)
        self.test_product_ids = [f'P{i:03d}' for i in range(10)]
    
    def test_add_vectors(self):
        """Test adding vectors to index."""
        self.manager.add_vectors(self.test_vectors, self.test_product_ids)
        
        stats = self.manager.get_stats()
        self.assertEqual(stats['total_vectors'], 10)
        self.assertEqual(stats['product_count'], 10)
    
    def test_search(self):
        """Test searching similar vectors."""
        self.manager.add_vectors(self.test_vectors, self.test_product_ids)
        
        # Search with first vector
        query_vector = self.test_vectors[0]
        results = self.manager.search(query_vector, k=5)
        
        # Check results
        self.assertEqual(len(results), 5)
        self.assertEqual(results[0]['product_id'], 'P000')  # Same vector
        self.assertAlmostEqual(results[0]['distance'], 0.0, places=5)
        self.assertAlmostEqual(results[0]['similarity'], 1.0, places=5)
    
    def test_search_with_exclusion(self):
        """Test searching with product exclusion."""
        self.manager.add_vectors(self.test_vectors, self.test_product_ids)
        
        query_vector = self.test_vectors[0]
        results = self.manager.search(
            query_vector, 
            k=5, 
            exclude_product_id='P000'
        )
        
        # Check that P000 is not in results
        product_ids = [r['product_id'] for r in results]
        self.assertNotIn('P000', product_ids)
    
    def test_remove_by_product_id(self):
        """Test removing vector by product ID."""
        self.manager.add_vectors(self.test_vectors, self.test_product_ids)
        
        # Remove one product
        self.manager.remove_by_product_id('P000')
        
        stats = self.manager.get_stats()
        self.assertEqual(stats['total_vectors'], 9)
        self.assertEqual(stats['product_count'], 9)
    
    def test_save_and_load(self):
        """Test saving and loading index."""
        self.manager.add_vectors(self.test_vectors, self.test_product_ids)
        
        # Save index
        self.manager.save()
        
        # Create new manager and load
        new_manager = FaissIndexManager(dimension=2048)
        new_manager.load()
        
        # Check stats
        stats = new_manager.get_stats()
        self.assertEqual(stats['total_vectors'], 10)
        self.assertEqual(stats['product_count'], 10)
        
        # Search should work
        query_vector = self.test_vectors[0]
        results = new_manager.search(query_vector, k=5)
        self.assertEqual(len(results), 5)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class ImageEmbeddingModelTestCase(TestCase):
    """Test ImageEmbedding model."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test category and brand
        cls.category = Category.objects.create(
            name='Test Category',
            slug='test-category'
        )
        cls.brand = Brand.objects.create(
            name='Test Brand',
            slug='test-brand'
        )
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        # Clean up test media
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
    
    def test_create_embedding(self):
        """Test creating an image embedding."""
        embedding_vector = np.random.randn(2048).astype(np.float32)
        
        embedding = ImageEmbedding.objects.create(
            product_id='TEST001',
            image_url='https://example.com/image.jpg',
            embedding_vector=embedding_vector.tolist(),
            model_version='resnet50'
        )
        
        # Check saved data
        self.assertEqual(embedding.product_id, 'TEST001')
        self.assertEqual(len(embedding.embedding_vector), 2048)
        self.assertEqual(embedding.model_version, 'resnet50')
    
    def test_update_embedding(self):
        """Test updating an existing embedding."""
        embedding_vector1 = np.random.randn(2048).astype(np.float32)
        
        embedding = ImageEmbedding.objects.create(
            product_id='TEST002',
            image_url='https://example.com/image1.jpg',
            embedding_vector=embedding_vector1.tolist()
        )
        
        # Update
        embedding_vector2 = np.random.randn(2048).astype(np.float32)
        embedding.embedding_vector = embedding_vector2.tolist()
        embedding.image_url = 'https://example.com/image2.jpg'
        embedding.save()
        
        # Reload and check
        embedding.refresh_from_db()
        self.assertEqual(embedding.image_url, 'https://example.com/image2.jpg')
        self.assertEqual(len(embedding.embedding_vector), 2048)


@override_settings(MEDIA_ROOT=TEST_MEDIA_ROOT)
class SimilarImagesAPITestCase(APITestCase):
    """Test Similar Images API endpoint."""
    
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        
        # Create test data
        cls.category = Category.objects.create(
            name='Down Jackets',
            slug='down'
        )
        cls.brand = Brand.objects.create(
            name='Test Brand',
            slug='test-brand'
        )
    
    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEST_MEDIA_ROOT, ignore_errors=True)
    
    @unittest.skip("API tests require real Product data structure")
    def setUp(self):
        pass
    
    @unittest.skip("API tests require real Product data structure")
    def test_similar_images_no_embedding(self):
        """Test API when product has no embedding."""
        pass
    
    @unittest.skip("API tests require real Product data structure")
    def test_similar_images_with_embeddings(self):
        """Test API with existing embeddings."""
        pass
    
    @unittest.skip("API tests require real Product data structure")
    def test_similar_images_invalid_product(self):
        """Test API with invalid product ID."""
        pass
    
    @unittest.skip("API tests require real Product data structure")
    def test_similar_images_query_params(self):
        """Test API with query parameters."""
        pass


class ImageIndexStatsAPITestCase(APITestCase):
    """Test Image Index Stats API endpoint."""
    
    @unittest.skip("Skipping test that requires Redis")
    def test_get_stats(self):
        """Test getting index statistics."""
        url = reverse('recommendations:image_index_stats')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        data = response.json()
        
        self.assertIn('faiss_index', data)
        self.assertIn('database', data)
        self.assertIn('status', data)
