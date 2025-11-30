"""
Product base model and category-specific models
"""
from django.db import models
from apps.core.models import Brand, Category


class ProductBase(models.Model):
    """추상 베이스 상품 모델"""
    id = models.CharField(max_length=100, primary_key=True, verbose_name='상품 ID')
    brand = models.ForeignKey(Brand, on_delete=models.CASCADE, verbose_name='브랜드')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, verbose_name='카테고리')
    
    title = models.CharField(max_length=500, verbose_name='제목')
    slug = models.SlugField(max_length=600, unique=True, verbose_name='URL 슬러그')
    image_url = models.URLField(max_length=2000, verbose_name='이미지 URL')
    
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='가격')
    original_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='원가')
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='할인율')
    currency = models.CharField(max_length=3, default='KRW', verbose_name='통화')
    
    seller = models.CharField(max_length=100, verbose_name='판매자')
    deeplink = models.URLField(max_length=2000, verbose_name='딥링크')
    in_stock = models.BooleanField(default=True, verbose_name='재고 있음')
    
    score = models.FloatField(default=0.0, verbose_name='신뢰도 점수')
    source = models.CharField(max_length=50, verbose_name='제휴사')
    
    material_composition = models.TextField(
        blank=True, 
        null=True, 
        verbose_name='소재 구성',
        help_text='예: polyester 40%, acrylic 20%, wool 4%'
    )
    
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='생성일')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='수정일')
    
    class Meta:
        abstract = True
        indexes = [
            models.Index(fields=['brand', 'category', '-discount_rate']),
            models.Index(fields=['in_stock', '-updated_at']),
            models.Index(fields=['-created_at']),
        ]
    
    def __str__(self):
        return self.title


class DownProduct(ProductBase):
    """다운 제품 모델"""
    DOWN_TYPE_CHOICES = [
        ('goose', '거위털'),
        ('duck', '오리털'),
        ('synthetic', '합성'),
    ]
    
    FIT_CHOICES = [
        ('slim', '슬림'),
        ('regular', '레귤러'),
        ('relaxed', '릴렉스'),
        ('oversized', '오버사이즈'),
    ]
    
    SHELL_CHOICES = [
        ('nylon', '나일론'),
        ('polyester', '폴리에스터'),
        ('gore-tex', '고어텍스'),
        ('cotton', '코튼'),
        ('wool', '울'),
    ]
    
    down_type = models.CharField(
        max_length=50, 
        choices=DOWN_TYPE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='다운 타입'
    )
    down_ratio = models.CharField(max_length=20, blank=True, null=True, verbose_name='다운 비율')
    fill_power = models.IntegerField(blank=True, null=True, verbose_name='필파워')
    hood = models.BooleanField(blank=True, null=True, verbose_name='후드')
    fit = models.CharField(
        max_length=50, 
        choices=FIT_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='핏'
    )
    shell = models.CharField(
        max_length=50, 
        choices=SHELL_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='소재'
    )
    
    class Meta:
        verbose_name = '다운 상품'
        verbose_name_plural = '다운 상품'
        indexes = [
            *ProductBase.Meta.indexes,
            models.Index(fields=['down_ratio', 'fill_power']),
            models.Index(fields=['hood', 'fit']),
        ]


class SlacksProduct(ProductBase):
    """슬랙스 제품 모델"""
    WAIST_TYPE_CHOICES = [
        ('high', '하이웨이스트'),
        ('mid', '미드웨이스트'),
        ('low', '로우웨이스트'),
    ]
    
    LEG_OPENING_CHOICES = [
        ('tapered', '테이퍼드'),
        ('straight', '스트레이트'),
        ('wide', '와이드'),
    ]
    
    PLEATS_CHOICES = [
        ('single', '싱글'),
        ('double', '더블'),
        ('none', '없음'),
    ]
    
    waist_type = models.CharField(
        max_length=50, 
        choices=WAIST_TYPE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='허리 높이'
    )
    leg_opening = models.CharField(
        max_length=50, 
        choices=LEG_OPENING_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='밑단 형태'
    )
    stretch = models.BooleanField(blank=True, null=True, verbose_name='신축성')
    pleats = models.CharField(
        max_length=50, 
        choices=PLEATS_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='주름'
    )
    fit = models.CharField(max_length=50, blank=True, null=True, verbose_name='핏')
    shell = models.CharField(max_length=50, blank=True, null=True, verbose_name='소재')
    
    class Meta:
        verbose_name = '슬랙스 상품'
        verbose_name_plural = '슬랙스 상품'
        indexes = [
            *ProductBase.Meta.indexes,
            models.Index(fields=['waist_type', 'leg_opening']),
        ]


class JeansProduct(ProductBase):
    """청바지 제품 모델"""
    WASH_CHOICES = [
        ('light', '라이트'),
        ('medium', '미디엄'),
        ('dark', '다크'),
        ('black', '블랙'),
    ]
    
    CUT_CHOICES = [
        ('skinny', '스키니'),
        ('slim', '슬림'),
        ('straight', '스트레이트'),
        ('bootcut', '부츠컷'),
        ('wide', '와이드'),
    ]
    
    RISE_CHOICES = [
        ('low', '로우라이즈'),
        ('mid', '미드라이즈'),
        ('high', '하이라이즈'),
    ]
    
    wash = models.CharField(
        max_length=50, 
        choices=WASH_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='워싱'
    )
    cut = models.CharField(
        max_length=50, 
        choices=CUT_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='컷'
    )
    rise = models.CharField(
        max_length=50, 
        choices=RISE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='라이즈'
    )
    stretch = models.BooleanField(blank=True, null=True, verbose_name='신축성')
    distressed = models.BooleanField(blank=True, null=True, verbose_name='디스트레스')
    
    class Meta:
        verbose_name = '청바지 상품'
        verbose_name_plural = '청바지 상품'
        indexes = [
            *ProductBase.Meta.indexes,
            models.Index(fields=['wash', 'cut']),
        ]


class CrewneckProduct(ProductBase):
    """크루넥 제품 모델"""
    NECKLINE_CHOICES = [
        ('crew', '크루넥'),
        ('mock', '목넥'),
        ('v-neck', 'V넥'),
        ('henley', '헨리넥'),
    ]
    
    SLEEVE_CHOICES = [
        ('short', '반팔'),
        ('long', '긴팔'),
    ]
    
    PATTERN_CHOICES = [
        ('solid', '무지'),
        ('stripe', '스트라이프'),
        ('graphic', '그래픽'),
    ]
    
    neckline = models.CharField(
        max_length=50, 
        choices=NECKLINE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='네크라인'
    )
    sleeve_length = models.CharField(
        max_length=50, 
        choices=SLEEVE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='소매 길이'
    )
    pattern = models.CharField(
        max_length=50, 
        choices=PATTERN_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='패턴'
    )
    fit = models.CharField(max_length=50, blank=True, null=True, verbose_name='핏')
    shell = models.CharField(max_length=50, blank=True, null=True, verbose_name='소재')
    
    class Meta:
        verbose_name = '크루넥 상품'
        verbose_name_plural = '크루넥 상품'


class LongSleeveProduct(ProductBase):
    """긴팔 제품 모델"""
    SLEEVE_TYPE_CHOICES = [
        ('raglan', '래글런'),
        ('set-in', '세트인'),
    ]
    
    neckline = models.CharField(max_length=50, blank=True, null=True, verbose_name='네크라인')
    sleeve_type = models.CharField(
        max_length=50, 
        choices=SLEEVE_TYPE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='소매 타입'
    )
    layering = models.BooleanField(blank=True, null=True, verbose_name='레이어링 가능')
    fit = models.CharField(max_length=50, blank=True, null=True, verbose_name='핏')
    shell = models.CharField(max_length=50, blank=True, null=True, verbose_name='소재')
    
    class Meta:
        verbose_name = '긴팔 상품'
        verbose_name_plural = '긴팔 상품'


class CoatProduct(ProductBase):
    """코트 제품 모델"""
    LENGTH_CHOICES = [
        ('short', '숏'),
        ('mid', '미디'),
        ('long', '롱'),
    ]
    
    CLOSURE_CHOICES = [
        ('button', '버튼'),
        ('zip', '지퍼'),
        ('belt', '벨트'),
    ]
    
    LINING_CHOICES = [
        ('full', '전체'),
        ('half', '부분'),
        ('none', '없음'),
    ]
    
    length = models.CharField(
        max_length=50, 
        choices=LENGTH_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='기장'
    )
    closure = models.CharField(
        max_length=50, 
        choices=CLOSURE_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='여밈'
    )
    lining = models.CharField(
        max_length=50, 
        choices=LINING_CHOICES, 
        blank=True, 
        null=True,
        verbose_name='안감'
    )
    hood = models.BooleanField(blank=True, null=True, verbose_name='후드')
    fit = models.CharField(max_length=50, blank=True, null=True, verbose_name='핏')
    shell = models.CharField(max_length=50, blank=True, null=True, verbose_name='소재')
    
    class Meta:
        verbose_name = '코트 상품'
        verbose_name_plural = '코트 상품'


class GenericProduct(ProductBase):
    """기타 제품 모델"""
    fit = models.CharField(max_length=50, blank=True, null=True, verbose_name='핏')
    shell = models.CharField(max_length=50, blank=True, null=True, verbose_name='소재')
    
    class Meta:
        verbose_name = '기타 상품'
        verbose_name_plural = '기타 상품'


class PriceHistory(models.Model):
    """가격 이력 모델
    
    매일 자정에 Celery Beat가 모든 상품의 현재 가격을 스냅샷으로 저장
    가격 차트 API와 가격 하락 알림에 사용
    """
    product_id = models.CharField(max_length=100, db_index=True, verbose_name='상품 ID')
    product_type = models.CharField(max_length=50, verbose_name='상품 타입')
    
    price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='가격')
    original_price = models.DecimalField(max_digits=10, decimal_places=0, verbose_name='원가')
    discount_rate = models.DecimalField(max_digits=5, decimal_places=2, verbose_name='할인율')
    
    recorded_at = models.DateTimeField(auto_now_add=True, db_index=True, verbose_name='기록 시간')
    
    class Meta:
        verbose_name = '가격 이력'
        verbose_name_plural = '가격 이력'
        ordering = ['-recorded_at']
        indexes = [
            models.Index(fields=['product_id', '-recorded_at']),
            models.Index(fields=['recorded_at']),
        ]
    
    def __str__(self):
        return f"{self.product_id} - {self.price}원 ({self.recorded_at.strftime('%Y-%m-%d')})"
