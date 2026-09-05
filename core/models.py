from django.db import models


class SiteSettings(models.Model):
    """Company and brand information — singleton."""

    brand_name = models.CharField(max_length=200, default='Elvessora')
    tagline = models.CharField(max_length=300, blank=True)
    logo = models.ImageField(upload_to='brand/', blank=True, null=True)
    brand_story = models.TextField(blank=True)
    about_company = models.TextField(blank=True)
    business_address = models.TextField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    whatsapp_number = models.CharField(max_length=20, blank=True)
    facebook_url = models.URLField(blank=True)
    instagram_url = models.URLField(blank=True)
    twitter_url = models.URLField(blank=True)
    youtube_url = models.URLField(blank=True)
    pinterest_url = models.URLField(blank=True)
    free_shipping_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, default=1999
    )
    default_shipping_charge = models.DecimalField(
        max_digits=10, decimal_places=2, default=99
    )
    tax_rate = models.DecimalField(max_digits=5, decimal_places=2, default=18.00)
    low_stock_threshold = models.PositiveIntegerField(default=5)
    estimated_delivery_days = models.CharField(max_length=50, default='3-5 business days')
    courier_partner = models.CharField(max_length=100, blank=True)

    # SEO / Open Graph defaults
    default_meta_title = models.CharField(max_length=70, blank=True)
    default_meta_description = models.CharField(max_length=160, blank=True)
    og_image = models.ImageField(upload_to='seo/', blank=True, null=True)
    default_currency = models.CharField(max_length=3, default='INR')

    class Meta:
        verbose_name = 'Store Settings'
        verbose_name_plural = 'Store Settings'

    def __str__(self):
        return self.brand_name

    @property
    def whatsapp_digits(self):
        """Digits-only number for wa.me links."""
        raw = self.whatsapp_number or self.phone or ''
        return ''.join(ch for ch in str(raw) if ch.isdigit())

    @property
    def whatsapp_url(self):
        digits = self.whatsapp_digits
        if not digits:
            return ''
        return f'https://wa.me/{digits}'

    @property
    def whatsapp_chat_url(self):
        """WhatsApp link with a default greeting message."""
        base = self.whatsapp_url
        if not base:
            return ''
        from urllib.parse import quote
        text = quote(f'Hi {self.brand_name}, I need help with perfumes')
        return f'{base}?text={text}'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomePageContent(models.Model):
    """Singleton — luxury homepage sections (editable from admin)."""

    hero_eyebrow = models.CharField(max_length=120, default='Experience the Art of')
    hero_title = models.CharField(max_length=200, default='Luxury\nFragrance')
    hero_description = models.TextField(
        default='Crafted with rare ingredients to leave a timeless impression.',
    )
    hero_image = models.ImageField(upload_to='homepage/', blank=True, null=True)
    hero_cta_primary_text = models.CharField(max_length=60, default='Explore Collection')
    hero_cta_secondary_text = models.CharField(max_length=60, default='Shop Now')

    collection_label = models.CharField(max_length=80, default='Our Collection')
    collection_heading = models.CharField(max_length=200, default='Find Your Signature Scent')

    excellence_label = models.CharField(max_length=80, default='Crafted With')
    excellence_heading = models.CharField(max_length=200, default='Excellence')
    excellence_text = models.TextField(
        default=(
            'Every Elvessora fragrance is composed with premium oils and refined accords — '
            'a balance of elegance, depth, and lasting presence.'
        ),
    )

    story_label = models.CharField(max_length=80, default='Our Story')
    story_heading = models.CharField(max_length=200, default='The Art of Timeless Luxury')
    story_text = models.TextField(blank=True)
    story_image = models.ImageField(upload_to='homepage/', blank=True, null=True)
    story_link_text = models.CharField(max_length=80, default='Discover Our Journey')

    show_favorites_picker = models.BooleanField(default=True)
    show_reviews = models.BooleanField(default=True)
    show_quiz_cta = models.BooleanField(default=True)

    class Meta:
        verbose_name = 'Homepage Content'
        verbose_name_plural = 'Homepage Content'

    def __str__(self):
        return 'Homepage Content'

    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def get(cls):
        obj, _ = cls.objects.get_or_create(pk=1)
        return obj


class HomePageHighlight(models.Model):
    """Repeatable homepage items: hero features, ingredients, value props."""

    HIGHLIGHT_TYPES = [
        ('hero_feature', 'Hero Feature'),
        ('ingredient', 'Ingredient'),
        ('value_prop', 'Value Proposition'),
    ]

    highlight_type = models.CharField(max_length=20, choices=HIGHLIGHT_TYPES)
    icon = models.CharField(
        max_length=60,
        default='bi-flower1',
        help_text='Bootstrap Icons class, e.g. bi-flower1',
    )
    title = models.CharField(max_length=100)
    subtitle = models.CharField(max_length=120, blank=True)
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['highlight_type', 'order']
        verbose_name = 'Homepage Highlight'
        verbose_name_plural = 'Homepage Highlights'

    def __str__(self):
        return f'{self.get_highlight_type_display()}: {self.title}'


class FAQ(models.Model):
    CATEGORY_CHOICES = [
        ('orders_shipping', 'Orders & Shipping'),
        ('products_ingredients', 'Products & Ingredients'),
        ('payments_offers', 'Payments & Offers'),
        ('returns_refunds', 'Returns & Refunds'),
        ('fragrance_guide', 'Fragrance Guide'),
        ('account_support', 'Account & Support'),
    ]

    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(
        max_length=30, choices=CATEGORY_CHOICES, default='account_support'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'

    def __str__(self):
        return self.question


class LegalPage(models.Model):
    PAGE_TYPES = [
        ('privacy', 'Privacy Policy'),
        ('terms', 'Terms & Conditions'),
        ('shipping', 'Shipping Policy'),
        ('returns', 'Return & Refund Policy'),
        ('cancellation', 'Cancellation Policy'),
        ('cookies', 'Cookie Policy'),
    ]

    page_type = models.CharField(max_length=20, choices=PAGE_TYPES, unique=True)
    title = models.CharField(max_length=200)
    content = models.TextField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Legal Page'
        verbose_name_plural = 'Legal Pages'

    def __str__(self):
        return self.title


class Country(models.Model):
    name = models.CharField(max_length=100)
    code = models.CharField(max_length=2, unique=True, help_text='ISO 2-letter code')
    phone_code = models.CharField(max_length=8, blank=True)
    is_active = models.BooleanField(default=True)
    tax_rate = models.DecimalField(
        max_digits=5, decimal_places=2, null=True, blank=True,
        help_text='Override store tax for this country (optional)',
    )

    class Meta:
        verbose_name_plural = 'Countries'
        ordering = ['name']

    def __str__(self):
        return self.name


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=60)
    symbol = models.CharField(max_length=8, default='AED')
    exchange_rate = models.DecimalField(
        max_digits=12, decimal_places=6, default=1,
        help_text='Rate vs store base currency',
    )
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Currencies'
        ordering = ['code']

    def save(self, *args, **kwargs):
        if self.is_default:
            Currency.objects.filter(is_default=True).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.code} ({self.symbol})'


class RegionPrice(models.Model):
    """Optional region-based product pricing override."""

    product = models.ForeignKey('products.Product', on_delete=models.CASCADE, related_name='region_prices')
    country = models.ForeignKey(Country, on_delete=models.CASCADE, related_name='region_prices')
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.ForeignKey(Currency, on_delete=models.PROTECT, related_name='region_prices')

    class Meta:
        unique_together = ['product', 'country']
        ordering = ['country__name']

    def __str__(self):
        return f'{self.product} — {self.country}: {self.price}'


class ShippingProvider(models.Model):
    name = models.CharField(max_length=120)
    tracking_url_template = models.CharField(
        max_length=300, blank=True,
        help_text='Use {tracking} placeholder, e.g. https://track.example/{tracking}',
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ShippingZone(models.Model):
    name = models.CharField(max_length=120)
    countries = models.ManyToManyField(Country, blank=True, related_name='shipping_zones')
    flat_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    free_shipping_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    estimated_days = models.CharField(max_length=50, blank=True, default='3-7 business days')
    provider = models.ForeignKey(
        ShippingProvider, on_delete=models.SET_NULL, null=True, blank=True, related_name='zones'
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        return self.name


class ActivityLog(models.Model):
    user = models.ForeignKey(
        'auth.User', on_delete=models.SET_NULL, null=True, blank=True, related_name='activity_logs'
    )
    action = models.CharField(max_length=120)
    object_repr = models.CharField(max_length=250, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.action} — {self.object_repr}'


class LoginHistory(models.Model):
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE, related_name='login_history')
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.CharField(max_length=300, blank=True)
    success = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Login history'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.user} @ {self.created_at:%Y-%m-%d %H:%M}'
