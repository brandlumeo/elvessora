from django.db import models


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-subscribed_at']

    def __str__(self):
        return self.email


class Banner(models.Model):
    POSITIONS = [
        ('hero', 'Homepage Hero'),
        ('secondary', 'Secondary Banner'),
        ('promo', 'Promotional Strip'),
    ]

    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    image = models.ImageField(upload_to='banners/')
    link_url = models.CharField(max_length=500, blank=True)
    button_text = models.CharField(max_length=50, blank=True, default='Shop Now')
    position = models.CharField(max_length=20, choices=POSITIONS, default='hero')
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class HomepageSection(models.Model):
    SECTION_TYPES = [
        ('best_sellers', 'Best Sellers'),
        ('new_arrivals', 'New Arrivals'),
        ('collections', 'Collections'),
        ('gift_sets', 'Gift Sets'),
        ('fragrance_families', 'Fragrance Families'),
        ('instagram', 'Instagram Feed'),
    ]

    section_type = models.CharField(max_length=30, choices=SECTION_TYPES, unique=True)
    title = models.CharField(max_length=200)
    subtitle = models.CharField(max_length=300, blank=True)
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return self.title


class PromoPopup(models.Model):
    title = models.CharField(max_length=200)
    content = models.TextField()
    coupon_code = models.CharField(max_length=50, blank=True)
    image = models.ImageField(upload_to='popups/', blank=True, null=True)
    is_active = models.BooleanField(default=True)
    show_once = models.BooleanField(default=True)

    def __str__(self):
        return self.title


class AbandonedCartReminder(models.Model):
    cart = models.ForeignKey('cart.Cart', on_delete=models.CASCADE, related_name='reminders')
    email = models.EmailField()
    sent_at = models.DateTimeField(auto_now_add=True)
    is_converted = models.BooleanField(default=False)

    class Meta:
        ordering = ['-sent_at']

    def __str__(self):
        return f'Reminder for {self.email}'


class ContactEnquiry(models.Model):
    ENQUIRY_TYPES = [
        ('general', 'General'),
        ('customer', 'Customer Message'),
        ('wholesale', 'Wholesale Enquiry'),
    ]

    name = models.CharField(max_length=150)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    subject = models.CharField(max_length=200)
    message = models.TextField()
    enquiry_type = models.CharField(max_length=20, choices=ENQUIRY_TYPES, default='general')
    is_read = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = 'Contact enquiries'
        ordering = ['-created_at']

    def __str__(self):
        return f'{self.subject} — {self.name}'


class FlashSale(models.Model):
    name = models.CharField(max_length=150)
    products = models.ManyToManyField('products.Product', blank=True, related_name='flash_sales')
    discount_percent = models.DecimalField(max_digits=5, decimal_places=2, default=10)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['-starts_at']

    def __str__(self):
        return self.name


class EmailCampaign(models.Model):
    STATUS = [
        ('draft', 'Draft'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
    ]

    subject = models.CharField(max_length=200)
    preview_text = models.CharField(max_length=200, blank=True)
    body_html = models.TextField(help_text='HTML email body')
    status = models.CharField(max_length=20, choices=STATUS, default='draft')
    scheduled_at = models.DateTimeField(null=True, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.subject
