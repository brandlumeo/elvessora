from django.contrib import admin
from django.utils.safestring import mark_safe
from .models import Review


@admin.action(description='Approve selected reviews')
def approve_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=True)


@admin.action(description='Reject selected reviews')
def reject_reviews(modeladmin, request, queryset):
    queryset.update(is_approved=False)


@admin.action(description='Mark as featured')
def feature_reviews(modeladmin, request, queryset):
    queryset.update(is_featured=True, is_approved=True)


@admin.action(description='Remove featured')
def unfeature_reviews(modeladmin, request, queryset):
    queryset.update(is_featured=False)


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'user', 'rating', 'is_approved', 'is_featured',
        'approval_status', 'created_at',
    ]
    list_filter = ['rating', 'is_approved', 'is_featured', 'created_at']
    list_editable = ['is_approved', 'is_featured']
    search_fields = ['product__name', 'user__username', 'comment', 'title']
    actions = [approve_reviews, reject_reviews, feature_reviews, unfeature_reviews]
    readonly_fields = ['product', 'user', 'rating', 'title', 'comment', 'created_at', 'updated_at']

    def approval_status(self, obj):
        if obj.is_approved:
            return mark_safe('<span class="elv-review-approved">Approved</span>')
        return mark_safe('<span class="elv-review-pending">Pending</span>')

    approval_status.short_description = 'Status'

    def has_add_permission(self, request):
        return False
