import pytest
from apps.core.models import Brand, Category


@pytest.mark.unit
class TestBrandModel:
    """Brand 모델 단위 테스트"""
    
    def test_create_brand(self, db):
        """브랜드 생성 테스트"""
        brand = Brand.objects.create(name='Nike')
        assert brand.name == 'Nike'
        assert brand.id is not None
        assert str(brand) == 'Nike'
    
    def test_brand_unique_constraint(self, db, sample_brand):
        """브랜드 이름 유니크 제약조건 테스트"""
        from django.db import IntegrityError
        
        with pytest.raises(IntegrityError):
            Brand.objects.create(name=sample_brand.name)
    
    def test_brand_str_representation(self, sample_brand):
        """브랜드 문자열 표현 테스트"""
        assert str(sample_brand) == sample_brand.name


@pytest.mark.unit
class TestCategoryModel:
    """Category 모델 단위 테스트"""
    
    def test_create_category(self, db):
        """카테고리 생성 테스트"""
        category = Category.objects.create(
            name='Outerwear',
            description='Jackets and coats'
        )
        assert category.name == 'Outerwear'
        assert category.description == 'Jackets and coats'
        assert category.id is not None
    
    def test_category_without_description(self, db):
        """설명 없이 카테고리 생성 테스트"""
        category = Category.objects.create(name='Tops')
        assert category.name == 'Tops'
        assert category.description == ''
    
    def test_category_str_representation(self, sample_category):
        """카테고리 문자열 표현 테스트"""
        assert str(sample_category) == sample_category.name
