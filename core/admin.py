from django.contrib import admin
from .models import (
    SiteSettings, HomePageContent, HomePageHighlight, FAQ, LegalPage,
    Country, Currency, RegionPrice, ShippingProvider, ShippingZone,
    ActivityLog, LoginHistory,
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Brand', {'fields': ('brand_name', 'tagline', 'logo', 'brand_story', 'about_company')}),
        ('Contact', {'fields': ('business_address', 'email', 'phone', 'whatsapp_number')}),
        ('Social Media', {'fields': ('facebook_url', 'instagram_url', 'twitter_url', 'youtube_url', 'pinterest_url')}),
        ('Commerce', {
            'fields': (
                'free_shipping_threshold', 'default_shipping_charge', 'tax_rate',
                'low_stock_threshold', 'estimated_delivery_days', 'courier_partner',
                'default_currency',
            ),
        }),
        ('SEO & Open Graph', {
            'fields': ('default_meta_title', 'default_meta_description', 'og_image'),
        }),
    )

    def has_add_permission(self, request):
        return not SiteSettings.objects.exists()


@admin.register(HomePageContent)
class HomePageContentAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Hero', {
            'fields': (
                'hero_eyebrow', 'hero_title', 'hero_description', 'hero_image',
                'hero_cta_primary_text', 'hero_cta_secondary_text',
            ),
        }),
        ('Collection', {'fields': ('collection_label', 'collection_heading')}),
        ('Excellence', {'fields': ('excellence_label', 'excellence_heading', 'excellence_text')}),
        ('Story', {
            'fields': (
                'story_label', 'story_heading', 'story_text', 'story_image', 'story_link_text',
            ),
        }),
        ('Lower Sections', {
            'fields': ('show_favorites_picker', 'show_reviews', 'show_quiz_cta'),
        }),
    )

    def has_add_permission(self, request):
        return not HomePageContent.objects.exists()


@admin.register(HomePageHighlight)
class HomePageHighlightAdmin(admin.ModelAdmin):
    list_display = ['title', 'highlight_type', 'icon', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['highlight_type']


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(LegalPage)
class LegalPageAdmin(admin.ModelAdmin):
    list_display = ['title', 'page_type', 'updated_at']


@admin.register(Country)
class CountryAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'phone_code', 'tax_rate', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name', 'code']
    list_editable = ['is_active']


@admin.register(Currency)
class CurrencyAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'symbol', 'exchange_rate', 'is_default', 'is_active']
    list_editable = ['exchange_rate', 'is_default', 'is_active']


@admin.register(RegionPrice)
class RegionPriceAdmin(admin.ModelAdmin):
    list_display = ['product', 'country', 'price', 'currency']
    list_filter = ['country', 'currency']
    search_fields = ['product__name']
    raw_id_fields = ['product']


@admin.register(ShippingProvider)
class ShippingProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'is_active']
    list_editable = ['is_active']


@admin.register(ShippingZone)
class ShippingZoneAdmin(admin.ModelAdmin):
    list_display = ['name', 'flat_rate', 'free_shipping_threshold', 'provider', 'is_active']
    list_filter = ['is_active', 'provider']
    filter_horizontal = ['countries']
    list_editable = ['is_active']


@admin.register(ActivityLog)
class ActivityLogAdmin(admin.ModelAdmin):
    list_display = ['action', 'object_repr', 'user', 'ip_address', 'created_at']
    list_filter = ['action', 'created_at']
    search_fields = ['action', 'object_repr', 'user__username']
    readonly_fields = ['user', 'action', 'object_repr', 'ip_address', 'created_at']

    def has_add_permission(self, request):
        return False


@admin.register(LoginHistory)
class LoginHistoryAdmin(admin.ModelAdmin):
    list_display = ['user', 'ip_address', 'success', 'created_at']
    list_filter = ['success', 'created_at']
    search_fields = ['user__username', 'ip_address']
    readonly_fields = ['user', 'ip_address', 'user_agent', 'success', 'created_at']

    def has_add_permission(self, request):
        return False
