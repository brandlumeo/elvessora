from django.db import models
from django.db.models import Avg
from django.urls import reverse
from django.utils.text import slugify


class Brand(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    logo = models.ImageField(upload_to='brands/', blank=True, null=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    parent = models.ForeignKey(
        'self',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='children',
    )
    image = models.ImageField(upload_to='categories/', blank=True, null=True)
    banner = models.ImageField(upload_to='categories/banners/', blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        if self.parent_id:
            return f'{self.parent.name} → {self.name}'
        return self.name


class Collection(models.Model):
    TYPE_CHOICES = [
        ('general', 'General'),
        ('seasonal', 'Seasonal'),
        ('luxury', 'Luxury'),
        ('gift', 'Gift'),
        ('featured', 'Featured'),
    ]

    name = models.CharField(max_length=150)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='collections/', blank=True, null=True)
    collection_type = models.CharField(
        max_length=20, choices=TYPE_CHOICES, default='general'
    )
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:collection_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class FragranceFamily(models.Model):
    FAMILIES = [
        ('woody', 'Woody'),
        ('floral', 'Floral'),
        ('fresh', 'Fresh'),
        ('citrus', 'Citrus'),
        ('fruity', 'Fruity'),
        ('oriental', 'Oriental/Amber'),
        ('oud', 'Oud'),
        ('musk', 'Musk'),
        ('aquatic', 'Aquatic'),
        ('spicy', 'Spicy'),
    ]

    name = models.CharField(max_length=50, choices=FAMILIES, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='families/', blank=True, null=True)

    class Meta:
        verbose_name_plural = 'Fragrance Families'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_name_display())
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:fragrance_family', kwargs={'slug': self.slug})

    def __str__(self):
        return self.get_name_display()


class Occasion(models.Model):
    OCCASIONS = [
        ('daily', 'Daily Wear'),
        ('office', 'Office'),
        ('date', 'Date Night'),
        ('party', 'Party'),
        ('wedding', 'Wedding'),
        ('special', 'Special Occasions'),
        ('summer', 'Summer'),
        ('winter', 'Winter'),
        ('day', 'Day Wear'),
        ('night', 'Night Wear'),
    ]

    name = models.CharField(max_length=50, choices=OCCASIONS, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    description = models.TextField(blank=True)
    image = models.ImageField(upload_to='occasions/', blank=True, null=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.get_name_display())
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('products:occasion', kwargs={'slug': self.slug})

    def __str__(self):
        return self.get_name_display()


class Product(models.Model):
    GENDER_CHOICES = [
        ('men', 'Men'),
        ('women', 'Women'),
        ('unisex', 'Unisex'),
    ]
    CONCENTRATION_CHOICES = [
        ('edp', 'Eau de Parfum (EDP)'),
        ('edt', 'Eau de Toilette (EDT)'),
        ('parfum', 'Parfum'),
        ('edc', 'Eau de Cologne (EDC)'),
        ('body_mist', 'Body Mist'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    sku = models.CharField(max_length=50, unique=True)
    barcode = models.CharField(max_length=64, blank=True)
    brand = models.ForeignKey(
        Brand, on_delete=models.SET_NULL, null=True, blank=True, related_name='products'
    )
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='products')
    collection = models.ForeignKey(Collection, on_delete=models.SET_NULL, null=True, blank=True, related_name='products')
    fragrance_families = models.ManyToManyField(FragranceFamily, blank=True, related_name='products')
    occasions = models.ManyToManyField(Occasion, blank=True, related_name='products')

    short_description = models.CharField(max_length=300, blank=True)
    description = models.TextField()
    tags = models.CharField(
        max_length=300,
        blank=True,
        help_text='Comma-separated tags (e.g. oud, evening, gift)',
    )
    top_notes = models.CharField(max_length=300, blank=True)
    heart_notes = models.CharField(max_length=300, blank=True)
    base_notes = models.CharField(max_length=300, blank=True)
    main_accords = models.CharField(
        max_length=500,
        blank=True,
        help_text='Format: accord:weight,accord:weight (e.g. floral:90,vanilla:75)',
    )
    concentration = models.CharField(max_length=20, choices=CONCENTRATION_CHOICES, default='edp')
    gender = models.CharField(max_length=10, choices=GENDER_CHOICES, default='unisex')
    longevity = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g. 6-8 hours, Long lasting',
    )
    sillage = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g. Moderate, Strong, Intimate',
    )
    ingredients = models.TextField(blank=True)
    country_of_origin = models.CharField(max_length=100, blank=True)
    usage_instructions = models.TextField(blank=True)

    regular_price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)

    is_best_seller = models.BooleanField(default=False)
    is_new_arrival = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)

    meta_description = models.CharField(max_length=300, blank=True)
    meta_title = models.CharField(max_length=70, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.offer_price if self.offer_price else self.regular_price

    @property
    def discount_percent(self):
        if self.offer_price and self.regular_price:
            return int((1 - self.offer_price / self.regular_price) * 100)
        return 0

    @property
    def default_variant(self):
        variant = self.variants.filter(stock_quantity__gt=0).first()
        return variant or self.variants.first()

    @property
    def in_stock(self):
        return self.variants.filter(stock_quantity__gt=0).exists()

    @property
    def total_stock(self):
        return sum(v.stock_quantity for v in self.variants.all())

    @property
    def average_rating(self):
        reviews = self.reviews.filter(is_approved=True)
        if reviews.exists():
            return round(reviews.aggregate(Avg('rating'))['rating__avg'], 1)
        return 0

    @property
    def primary_image(self):
        img = self.images.filter(is_primary=True).first()
        return img if img else self.images.first()

    def get_absolute_url(self):
        return reverse('products:product_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class ProductVariant(models.Model):
    SIZE_CHOICES = [
        ('30ml', '30ml'),
        ('50ml', '50ml'),
        ('75ml', '75ml'),
        ('100ml', '100ml'),
        ('150ml', '150ml'),
        ('200ml', '200ml'),
    ]

    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='variants')
    size = models.CharField(max_length=10, choices=SIZE_CHOICES)
    sku = models.CharField(max_length=50, unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    stock_quantity = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name = 'Inventory Item'
        verbose_name_plural = 'Inventory'
        unique_together = ['product', 'size']
        ordering = ['size']

    @property
    def current_price(self):
        return self.offer_price if self.offer_price else self.price

    @property
    def in_stock(self):
        return self.stock_quantity > 0

    def __str__(self):
        return f'{self.product.name} - {self.size}'


class ProductImage(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to='products/')
    alt_text = models.CharField(max_length=200, blank=True)
    is_primary = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.product.name} - Image {self.order}'


class ProductVideo(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='videos')
    video_url = models.URLField(help_text='YouTube or Vimeo URL')
    title = models.CharField(max_length=200, blank=True)

    def __str__(self):
        return f'{self.product.name} - Video'


class ProductImage360(models.Model):
    product = models.ForeignKey(Product, on_delete=models.CASCADE, related_name='images_360')
    image = models.ImageField(upload_to='products/360/')
    frame_order = models.PositiveIntegerField(default=0)
    alt_text = models.CharField(max_length=200, blank=True)

    class Meta:
        ordering = ['frame_order']
        verbose_name = '360° image'
        verbose_name_plural = '360° images'

    def __str__(self):
        return f'{self.product.name} — 360 frame {self.frame_order}'


class GiftSet(models.Model):
    GIFT_TYPES = [
        ('box', 'Perfume Gift Box'),
        ('multi', 'Multiple Perfume Set'),
        ('mini', 'Miniature Collection'),
        ('combo', 'Perfume & Body Spray Combo'),
    ]

    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    gift_type = models.CharField(max_length=20, choices=GIFT_TYPES)
    description = models.TextField()
    products = models.ManyToManyField(Product, related_name='gift_sets')
    regular_price = models.DecimalField(max_digits=10, decimal_places=2)
    offer_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    image = models.ImageField(upload_to='gift_sets/', blank=True, null=True)
    custom_wrapping_available = models.BooleanField(default=True)
    personalized_message_available = models.BooleanField(default=True)
    stock_quantity = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    @property
    def current_price(self):
        return self.offer_price if self.offer_price else self.regular_price

    @property
    def display_image_url(self):
        """Prefer gift-set upload; else first included product bottle image."""
        if self.image:
            try:
                return self.image.url
            except ValueError:
                pass
        product = self.products.select_related().prefetch_related('images').first()
        if product:
            primary = product.primary_image
            if primary and primary.image:
                try:
                    return primary.image.url
                except ValueError:
                    pass
        return ''

    def get_absolute_url(self):
        return reverse('products:gift_set_detail', kwargs={'slug': self.slug})

    def __str__(self):
        return self.name


class RecentlyViewed(models.Model):
    user = models.ForeignKey(
        'auth.User', on_delete=models.CASCADE, null=True, blank=True
    )
    session_key = models.CharField(max_length=40, blank=True)
    product = models.ForeignKey(Product, on_delete=models.CASCADE)
    viewed_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-viewed_at']
