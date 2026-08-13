from django.contrib import admin
from .models import Cart, CartItem


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'session_key', 'item_count_display', 'updated_at']
    inlines = [CartItemInline]

    def item_count_display(self, obj):
        return obj.item_count
    item_count_display.short_description = 'Items'
