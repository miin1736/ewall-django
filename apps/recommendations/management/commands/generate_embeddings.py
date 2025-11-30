"""
Management command to generate image embeddings for all products.

Usage:
    python manage.py generate_embeddings
    python manage.py generate_embeddings --batch-size 16
    python manage.py generate_embeddings --rebuild
    python manage.py generate_embeddings --category down
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from django.utils import timezone
from apps.products.models import (
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct
)
from apps.recommendations.models import ImageEmbedding
from apps.recommendations.services.image_embedding import ImageEmbeddingService
from apps.recommendations.services.faiss_manager import FaissIndexManager
import numpy as np
import logging

logger = logging.getLogger(__name__)

# All product models
PRODUCT_MODELS = [
    DownProduct, SlacksProduct, JeansProduct,
    CrewneckProduct, LongSleeveProduct, CoatProduct
]


class Command(BaseCommand):
    help = 'Generate image embeddings for all products and build Faiss index'

    def add_arguments(self, parser):
        parser.add_argument(
            '--batch-size',
            type=int,
            default=32,
            help='Batch size for processing images (default: 32)'
        )
        parser.add_argument(
            '--rebuild',
            action='store_true',
            help='Rebuild all embeddings from scratch'
        )
        parser.add_argument(
            '--category',
            type=str,
            help='Only process products from specific category (slug)'
        )
        parser.add_argument(
            '--limit',
            type=int,
            help='Limit number of products to process'
        )
        parser.add_argument(
            '--model-version',
            type=str,
            default='resnet50',
            help='Model version to use (default: resnet50)'
        )

    def handle(self, *args, **options):
        batch_size = options['batch_size']
        rebuild = options['rebuild']
        category_slug = options.get('category')
        limit = options.get('limit')
        model_version = options['model_version']
        
        self.stdout.write(self.style.SUCCESS(
            f'\n=== Image Embedding Generation ==='
        ))
        self.stdout.write(f'Batch size: {batch_size}')
        self.stdout.write(f'Model version: {model_version}')
        self.stdout.write(f'Rebuild mode: {rebuild}')
        
        # Get products with images from all models
        products_list = []
        for model in PRODUCT_MODELS:
            query = model.objects.exclude(
                Q(image_url='') | Q(image_url__isnull=True)
            ).filter(in_stock=True)
            
            if category_slug:
                query = query.filter(category__slug=category_slug)
            
            products_list.extend(list(query))
        
        # Apply limit
        if limit:
            products_list = products_list[:limit]
            self.stdout.write(f'Limit: {limit}')
        
        if category_slug:
            self.stdout.write(f'Category filter: {category_slug}')
        
        total_products = len(products_list)
        self.stdout.write(f'Total products to process: {total_products}\n')
        
        if total_products == 0:
            self.stdout.write(self.style.WARNING('No products found to process'))
            return
        
        # Initialize services
        embedding_service = ImageEmbeddingService()
        faiss_manager = FaissIndexManager()
        
        # Track statistics
        stats = {
            'total': total_products,
            'processed': 0,
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'start_time': timezone.now()
        }
        
        # Process products in batches (products_list already created above)
        for i in range(0, len(products_list), batch_size):
            batch = products_list[i:i + batch_size]
            batch_num = (i // batch_size) + 1
            total_batches = (len(products_list) + batch_size - 1) // batch_size
            
            self.stdout.write(
                self.style.MIGRATE_HEADING(
                    f'\nProcessing batch {batch_num}/{total_batches} '
                    f'({len(batch)} products)'
                )
            )
            
            for product in batch:
                stats['processed'] += 1
                
                # Check if embedding already exists
                if not rebuild:
                    existing = ImageEmbedding.objects.filter(
                        product_id=product.id,
                        model_version=model_version
                    ).exists()
                    
                    if existing:
                        self.stdout.write(
                            f'  [{stats["processed"]}/{stats["total"]}] '
                            f'Skipping {product.id} (already exists)'
                        )
                        stats['skipped'] += 1
                        continue
                
                # Generate embedding
                try:
                    self.stdout.write(
                        f'  [{stats["processed"]}/{stats["total"]}] '
                        f'Processing {product.id}... ',
                        ending=''
                    )
                    
                    embedding_vector = embedding_service.get_embedding_from_url(
                        product.image_url,
                        use_cache=False  # Don't use cache during batch generation
                    )
                    
                    if embedding_vector is not None:
                        # Save to database
                        ImageEmbedding.objects.update_or_create(
                            product_id=product.id,
                            defaults={
                                'image_url': product.image_url,
                                'embedding_vector': embedding_vector.tolist(),
                                'model_version': model_version
                            }
                        )
                        
                        stats['success'] += 1
                        self.stdout.write(self.style.SUCCESS('✓'))
                    else:
                        stats['failed'] += 1
                        self.stdout.write(self.style.ERROR('✗ Failed'))
                        
                except Exception as e:
                    stats['failed'] += 1
                    self.stdout.write(
                        self.style.ERROR(f'✗ Error: {str(e)[:50]}')
                    )
                    logger.error(
                        f'Error processing {product.id}: {str(e)}',
                        exc_info=True
                    )
            
            # Show batch progress
            success_rate = (stats['success'] / stats['processed'] * 100) if stats['processed'] > 0 else 0
            self.stdout.write(
                f'  Batch complete: {stats["success"]} success, '
                f'{stats["failed"]} failed, {stats["skipped"]} skipped '
                f'({success_rate:.1f}% success rate)'
            )
        
        # Build Faiss index
        self.stdout.write(
            self.style.MIGRATE_HEADING('\n=== Building Faiss Index ===')
        )
        
        try:
            # Get all embeddings from database
            all_embeddings = ImageEmbedding.objects.filter(
                model_version=model_version
            )
            
            if all_embeddings.count() == 0:
                self.stdout.write(
                    self.style.WARNING('No embeddings found to index')
                )
                return
            
            # Prepare vectors and product IDs
            vectors = []
            product_ids = []
            
            for embedding in all_embeddings:
                vectors.append(np.array(embedding.embedding_vector, dtype=np.float32))
                product_ids.append(embedding.product_id)
            
            vectors = np.array(vectors, dtype=np.float32)
            
            self.stdout.write(f'Indexing {len(vectors)} embeddings...')
            
            # Clear existing index and add all vectors
            faiss_manager.index.reset()
            faiss_manager.product_ids = []
            faiss_manager.add_vectors(vectors, product_ids)
            
            # Save index to disk
            faiss_manager.save()
            
            self.stdout.write(self.style.SUCCESS('✓ Index built and saved'))
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'✗ Failed to build index: {str(e)}')
            )
            logger.error(f'Error building Faiss index: {str(e)}', exc_info=True)
        
        # Print final statistics
        elapsed = timezone.now() - stats['start_time']
        elapsed_seconds = elapsed.total_seconds()
        
        self.stdout.write(
            self.style.SUCCESS(
                f'\n=== Generation Complete ==='
            )
        )
        self.stdout.write(f'Total processed: {stats["processed"]}')
        self.stdout.write(
            self.style.SUCCESS(f'Successful: {stats["success"]}')
        )
        if stats['failed'] > 0:
            self.stdout.write(
                self.style.ERROR(f'Failed: {stats["failed"]}')
            )
        if stats['skipped'] > 0:
            self.stdout.write(
                self.style.WARNING(f'Skipped: {stats["skipped"]}')
            )
        self.stdout.write(f'Elapsed time: {elapsed_seconds:.1f}s')
        
        if stats['processed'] > 0:
            avg_time = elapsed_seconds / stats['processed']
            self.stdout.write(f'Average time per product: {avg_time:.2f}s')
        
        # Show index stats
        index_stats = faiss_manager.get_stats()
        self.stdout.write(f'\nFaiss index stats:')
        self.stdout.write(f'  Total vectors: {index_stats["total_vectors"]}')
        self.stdout.write(f'  Dimension: {index_stats["dimension"]}')
        self.stdout.write(f'  Product count: {index_stats["product_count"]}')
