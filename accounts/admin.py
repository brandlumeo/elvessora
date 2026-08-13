from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import Customer, UserProfile, Address, Wishlist


@admin.register(Customer)
class CustomerAdmin(BaseUserAdmin):
    """Registered store customers — name, email, phone."""

    list_display = ['full_name_display', 'email', 'phone_display', 'username', 'date_joined', 'is_active']
    list_filter = ['is_active', 'date_joined']
    search_fields = ['username', 'email', 'first_name', 'last_name', 'profile__phone']
    ordering = ['-date_joined']
    readonly_fields = ['username', 'email', 'first_name', 'last_name', 'date_joined', 'last_login']

    fieldsets = (
        ('Customer Info', {'fields': ('username', 'email', 'first_name', 'last_name', 'is_active')}),
        ('Activity', {'fields': ('date_joined', 'last_login')}),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).filter(is_staff=False).select_related('profile')

    def full_name_display(self, obj):
        return obj.get_full_name() or obj.username

    full_name_display.short_description = 'Name'

    def phone_display(self, obj):
        if hasattr(obj, 'profile') and obj.profile.phone:
            return obj.profile.phone
        return '—'

    phone_display.short_description = 'Phone'

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(UserProfile)
class UserProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone', 'loyalty_points', 'google_sub_display']
    search_fields = ['user__username', 'user__email', 'phone']
    raw_id_fields = ['user']
    list_editable = ['loyalty_points']

    def google_sub_display(self, obj):
        return 'Yes' if getattr(obj, 'google_sub', None) else '—'

    google_sub_display.short_description = 'Google linked'


@admin.register(Address)
class AddressAdmin(admin.ModelAdmin):
    list_display = ['user', 'full_name', 'city', 'state', 'pincode', 'is_default']
    list_filter = ['is_default', 'state']
    search_fields = ['user__username', 'full_name', 'city', 'pincode']
    raw_id_fields = ['user']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['owner_display', 'product', 'added_at']
    search_fields = ['user__username', 'session_key', 'product__name']
    raw_id_fields = ['user', 'product']
    list_filter = ['added_at']

    @admin.display(description='Owner')
    def owner_display(self, obj):
        if obj.user_id:
            return obj.user.get_username()
        return f'Guest ({obj.session_key[:8]}…)' if obj.session_key else 'Guest'
