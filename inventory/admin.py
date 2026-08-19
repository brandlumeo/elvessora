from django.contrib import admin
from django.utils.safestring import mark_safe
from core.models import SiteSettings
from .models import Inventory, Warehouse, StockAdjustment


@admin.register(Inventory)
class InventoryAdmin(admin.ModelAdmin):
    change_list_template = 'admin/inventory/change_list.html'

    list_display = [
        'product', 'size', 'sku', 'current_price_display',
        'stock_quantity', 'stock_status', 'in_stock_display',
    ]
    list_filter = ['size', 'product__category']
    search_fields = ['product__name', 'sku']
    list_editable = ['stock_quantity']
    ordering = ['product__name', 'size']
    list_per_page = 25

    fieldsets = (
        ('Product Variant', {'fields': ('product', 'size', 'sku')}),
        ('Pricing', {'fields': ('price', 'offer_price')}),
        ('Stock', {'fields': ('stock_quantity',)}),
    )

    def current_price_display(self, obj):
        return f'AED {obj.current_price}'

    current_price_display.short_description = 'Price'

    def stock_status(self, obj):
        threshold = SiteSettings.get().low_stock_threshold
        if obj.stock_quantity == 0:
            return mark_safe('<span class="elv-inv-out">Out of Stock</span>')
        if obj.stock_quantity <= threshold:
            return mark_safe('<span class="elv-inv-low">Low Stock</span>')
        return mark_safe('<span class="elv-inv-ok">In Stock</span>')

    stock_status.short_description = 'Alert'

    def in_stock_display(self, obj):
        return 'Yes' if obj.in_stock else 'No'

    in_stock_display.short_description = 'Available'

    def has_add_permission(self, request):
        return False

    def _log_stock_set(self, request, variant_id, before_qty, after_qty, note):
        if before_qty == after_qty:
            return
        adj = StockAdjustment(
            variant_id=variant_id,
            adjustment_type='set',
            quantity_change=after_qty,
            quantity_before=before_qty,
            quantity_after=after_qty,
            note=note,
            created_by=request.user,
        )
        adj.save(apply_stock=False)

    def save_model(self, request, obj, form, change):
        before = None
        if change and obj.pk:
            before = Inventory.objects.filter(pk=obj.pk).values_list('stock_quantity', flat=True).first()
        super().save_model(request, obj, form, change)
        if before is not None:
            self._log_stock_set(
                request, obj.pk, before, obj.stock_quantity,
                'Quick edit from Inventory admin',
            )

    def changelist_view(self, request, extra_context=None):
        extra_context = extra_context or {}
        threshold = SiteSettings.get().low_stock_threshold
        qs = Inventory.objects.all()
        extra_context['total_items'] = qs.count()
        extra_context['low_stock_count'] = qs.filter(
            stock_quantity__lte=threshold
        ).exclude(stock_quantity=0).count()
        extra_context['out_of_stock_count'] = qs.filter(stock_quantity=0).count()
        extra_context['low_stock_threshold'] = threshold

        before_map = None
        if request.method == 'POST':
            before_map = {
                pk: qty for pk, qty in Inventory.objects.values_list('id', 'stock_quantity')
            }

        response = super().changelist_view(request, extra_context=extra_context)

        if before_map is not None and request.user.is_authenticated:
            after_map = {
                pk: qty for pk, qty in Inventory.objects.values_list('id', 'stock_quantity')
            }
            for pk, after_qty in after_map.items():
                before_qty = before_map.get(pk)
                if before_qty is not None and before_qty != after_qty:
                    self._log_stock_set(
                        request, pk, before_qty, after_qty,
                        'Quick edit from Inventory list',
                    )
        return response


@admin.register(Warehouse)
class WarehouseAdmin(admin.ModelAdmin):
    list_display = ['name', 'code', 'city', 'country', 'is_default', 'is_active']
    list_editable = ['is_default', 'is_active']
    search_fields = ['name', 'code']


@admin.register(StockAdjustment)
class StockAdjustmentAdmin(admin.ModelAdmin):
    list_display = [
        'variant', 'warehouse', 'adjustment_type', 'quantity_change',
        'quantity_before', 'quantity_after', 'created_by', 'created_at',
    ]
    list_filter = ['adjustment_type', 'warehouse', 'created_at']
    search_fields = ['variant__sku', 'variant__product__name', 'note']
    raw_id_fields = ['variant']
    readonly_fields = ['quantity_before', 'quantity_after', 'created_at', 'created_by']

    def get_readonly_fields(self, request, obj=None):
        if obj:
            return [
                'variant', 'warehouse', 'adjustment_type', 'quantity_change',
                'note', 'quantity_before', 'quantity_after', 'created_by', 'created_at',
            ]
        return list(self.readonly_fields)

    def save_model(self, request, obj, form, change):
        if not change and not obj.created_by_id:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
