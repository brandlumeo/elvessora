from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver


class Customer(User):
    """Proxy model — registered customers only (non-staff)."""

    class Meta:
        proxy = True
        verbose_name = 'Customer'
        verbose_name_plural = 'Customers'


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone = models.CharField(max_length=20, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    newsletter_subscribed = models.BooleanField(default=False)
    loyalty_points = models.PositiveIntegerField(default=0)
    google_sub = models.CharField(max_length=255, blank=True, null=True, unique=True)

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username}'


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    if hasattr(instance, 'profile'):
        instance.profile.save()


class Address(models.Model):
    ADDRESS_TYPES = [
        ('home', 'Home'),
        ('office', 'Office'),
        ('other', 'Other'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='addresses')
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default='home')
    full_name = models.CharField(max_length=150)
    phone = models.CharField(max_length=20)
    address_line1 = models.CharField(max_length=255)
    address_line2 = models.CharField(max_length=255, blank=True)
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    pincode = models.CharField(max_length=10)
    country = models.CharField(max_length=100, default='India')
    is_default = models.BooleanField(default=False)

    class Meta:
        verbose_name_plural = 'Addresses'
        ordering = ['-is_default', '-id']

    def save(self, *args, **kwargs):
        if self.is_default:
            Address.objects.filter(user=self.user, is_default=True).update(is_default=False)
        super().save(*args, **kwargs)

    def __str__(self):
        return f'{self.full_name} - {self.city}'


class Wishlist(models.Model):
    """Wishlist works for guests (session) and logged-in users — same idea as cart."""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, null=True, blank=True, related_name='wishlist_items'
    )
    session_key = models.CharField(max_length=40, blank=True, db_index=True)
    product = models.ForeignKey('products.Product', on_delete=models.CASCADE)
    added_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-added_at']
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'product'],
                condition=models.Q(user__isnull=False),
                name='wishlist_user_product_uniq',
            ),
            models.UniqueConstraint(
                fields=['session_key', 'product'],
                condition=models.Q(user__isnull=True) & ~models.Q(session_key=''),
                name='wishlist_session_product_uniq',
            ),
        ]

    def __str__(self):
        owner = self.user.username if self.user_id else f'session:{self.session_key[:8]}'
        return f'{owner} - {self.product.name}'
