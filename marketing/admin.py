import csv

from django.contrib import admin
from django.http import HttpResponse

from .models import (
    NewsletterSubscriber, Banner, HomepageSection, PromoPopup,
    AbandonedCartReminder, ContactEnquiry, FlashSale, EmailCampaign,
)


@admin.action(description='Export selected subscribers to CSV')
def export_subscribers_csv(modeladmin, request, queryset):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="newsletter_subscribers.csv"'
    writer = csv.writer(response)
    writer.writerow(['Email', 'Active', 'Subscribed At'])
    for row in queryset.order_by('-subscribed_at'):
        writer.writerow([
            row.email,
            'Yes' if row.is_active else 'No',
            row.subscribed_at.isoformat(sep=' ', timespec='seconds'),
        ])
    return response


@admin.register(NewsletterSubscriber)
class NewsletterSubscriberAdmin(admin.ModelAdmin):
    list_display = ['email', 'is_active', 'subscribed_at']
    list_filter = ['is_active']
    search_fields = ['email']
    actions = [export_subscribers_csv]


@admin.register(Banner)
class BannerAdmin(admin.ModelAdmin):
    list_display = ['title', 'position', 'order', 'is_active']
    list_editable = ['order', 'is_active']
    list_filter = ['position']


@admin.register(HomepageSection)
class HomepageSectionAdmin(admin.ModelAdmin):
    list_display = ['title', 'section_type', 'order', 'is_active']
    list_editable = ['order', 'is_active']


@admin.register(PromoPopup)
class PromoPopupAdmin(admin.ModelAdmin):
    list_display = ['title', 'coupon_code', 'is_active']


@admin.register(AbandonedCartReminder)
class AbandonedCartReminderAdmin(admin.ModelAdmin):
    list_display = ['email', 'cart', 'sent_at', 'is_converted']
    list_filter = ['is_converted', 'sent_at']


@admin.action(description='Mark selected as read')
def mark_enquiries_read(modeladmin, request, queryset):
    queryset.update(is_read=True)


@admin.action(description='Mark selected as unread')
def mark_enquiries_unread(modeladmin, request, queryset):
    queryset.update(is_read=False)


@admin.register(ContactEnquiry)
class ContactEnquiryAdmin(admin.ModelAdmin):
    list_display = ['subject', 'name', 'email', 'enquiry_type', 'is_read', 'created_at']
    list_filter = ['enquiry_type', 'is_read', 'created_at']
    search_fields = ['name', 'email', 'subject', 'message']
    list_editable = ['is_read']
    readonly_fields = ['name', 'email', 'phone', 'subject', 'message', 'enquiry_type', 'created_at']
    actions = [mark_enquiries_read, mark_enquiries_unread]
    date_hierarchy = 'created_at'

    def has_add_permission(self, request):
        return False


@admin.register(FlashSale)
class FlashSaleAdmin(admin.ModelAdmin):
    list_display = ['name', 'discount_percent', 'starts_at', 'ends_at', 'is_active']
    list_filter = ['is_active']
    filter_horizontal = ['products']
    list_editable = ['is_active']


@admin.register(EmailCampaign)
class EmailCampaignAdmin(admin.ModelAdmin):
    list_display = ['subject', 'status', 'scheduled_at', 'sent_at', 'created_at']
    list_filter = ['status']
    search_fields = ['subject']
