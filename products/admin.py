from django.contrib import admin
from django.utils.html import format_html
from .models import (
    Brand, Category, Collection, FragranceFamily, Occasion, Product,
    ProductVariant, ProductImage, ProductVideo, ProductImage360, GiftSet, RecentlyViewed,
)


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 1


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ('image', 'preview', 'alt_text', 'is_primary', 'order')
    readonly_fields = ('preview',)

    @admin.display(description='Preview')
    def preview(self, obj):
        if obj.pk and obj.image:
            return format_html(
                '<img src="{}" alt="" style="max-height:72px;max-width:72px;object-fit:contain;border-radius:6px;background:#f5f5f5;" />',
                obj.image.url,
            )
        return '—'


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0


class ProductImage360Inline(admin.TabularInline):
    model = ProductImage360
    extra = 0
    fields = ('image', 'frame_order', 'alt_text')


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_active']
    list_filter = ['is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'slug', 'is_active']
    list_filter = ['is_active', 'parent']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ['name', 'collection_type', 'is_featured', 'slug', 'is_active']
    list_filter = ['collection_type', 'is_featured', 'is_active']
    search_fields = ['name']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_featured', 'is_active']


@admin.register(FragranceFamily)
class FragranceFamilyAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']


@admin.register(Occasion)
class OccasionAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'sku', 'brand', 'category', 'current_price_display',
        'total_stock_display', 'is_active', 'is_best_seller', 'is_new_arrival',
    ]
    list_filter = [
        'brand', 'category', 'gender', 'concentration',
        'is_active', 'is_best_seller', 'is_new_arrival', 'fragrance_families',
    ]
    search_fields = ['name', 'sku', 'barcode', 'description', 'short_description', 'tags']
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ['fragrance_families', 'occasions']
    inlines = [ProductVariantInline, ProductImageInline, ProductVideoInline, ProductImage360Inline]
    list_editable = ['is_active', 'is_best_seller', 'is_new_arrival']

    fieldsets = (
        ('Basic Info', {
            'fields': (
                'name', 'slug', 'sku', 'barcode', 'brand',
                'category', 'collection', 'short_description', 'description', 'tags',
            ),
        }),
        ('Fragrance Details', {
            'fields': (
                'top_notes', 'heart_notes', 'base_notes', 'main_accords',
                'concentration', 'gender', 'longevity', 'sillage',
                'fragrance_families', 'occasions',
            ),
        }),
        ('Additional Info', {
            'fields': (
                'ingredients', 'country_of_origin', 'usage_instructions',
                'meta_title', 'meta_description',
            ),
        }),
        ('Pricing', {'fields': ('regular_price', 'offer_price')}),
        ('Flags', {'fields': ('is_best_seller', 'is_new_arrival', 'is_featured', 'is_active')}),
    )

    def current_price_display(self, obj):
        return f'AED {obj.current_price}'
    current_price_display.short_description = 'Price'

    def total_stock_display(self, obj):
        stock = obj.total_stock
        color = 'red' if stock <= 5 else 'green'
        return format_html('<span style="color:{}">{}</span>', color, stock)
    total_stock_display.short_description = 'Stock'


@admin.register(GiftSet)
class GiftSetAdmin(admin.ModelAdmin):
    list_display = ['name', 'gift_type', 'image_preview', 'current_price', 'stock_quantity', 'is_active']
    list_filter = ['gift_type', 'is_active']
    search_fields = ['name', 'description']
    filter_horizontal = ['products']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    readonly_fields = ('image_preview_large',)
    fieldsets = (
        ('Gift Set Details', {
            'fields': ('name', 'slug', 'gift_type', 'description', 'products'),
        }),
        ('Image (shown on homepage Gift Sets section)', {
            'fields': ('image', 'image_preview_large'),
            'description': 'Upload a square or portrait gift-set photo. This image appears under Luxury Gift Sets on the homepage.',
        }),
        ('Pricing & Stock', {
            'fields': ('regular_price', 'offer_price', 'stock_quantity'),
        }),
        ('Options', {
            'fields': (
                'custom_wrapping_available',
                'personalized_message_available',
                'is_active',
            ),
        }),
    )

    def save_related(self, request, form, formsets, change):
        super().save_related(request, form, formsets, change)
        obj = form.instance
        if obj.pk and not obj.products.exists():
            from django.contrib import messages
            messages.warning(
                request,
                'This gift set has no products linked yet. Link at least one perfume '
                'so customers can add it to cart and so images can fall back to product photos.',
            )

    @admin.display(description='Image')
    def image_preview(self, obj):
        if obj.image:
            try:
                return format_html(
                    '<img src="{}" alt="" style="height:48px;width:48px;object-fit:cover;border-radius:6px;" />',
                    obj.image.url,
                )
            except ValueError:
                pass
        return format_html('<span style="color:#999;">{}</span>', 'No image')

    @admin.display(description='Preview')
    def image_preview_large(self, obj):
        if obj.pk and obj.image:
            try:
                return format_html(
                    '<img src="{}" alt="" style="max-height:180px;max-width:180px;object-fit:contain;border-radius:10px;background:#f5f5f5;padding:8px;" />',
                    obj.image.url,
                )
            except ValueError:
                pass
        return 'Upload an image above, then save to see preview.'


@admin.register(RecentlyViewed)
class RecentlyViewedAdmin(admin.ModelAdmin):
    list_display = ['product', 'user', 'viewed_at']
    list_filter = ['viewed_at']
