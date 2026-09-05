from django.shortcuts import render, get_object_or_404, redirect
from django.core.mail import send_mail
from django.conf import settings
from django.contrib import messages
from django.http import HttpResponse
from django.utils import timezone
from .models import SiteSettings, FAQ, LegalPage
from .homepage_context import build_luxury_page_context
from marketing.forms import ContactForm, NewsletterForm
from marketing.models import NewsletterSubscriber, Banner, HomepageSection, ContactEnquiry
from products.models import Product, Collection, FragranceFamily, GiftSet, Occasion


def home(request):
    banners = Banner.objects.filter(is_active=True, position='hero')
    best_sellers = Product.objects.filter(is_active=True, is_best_seller=True)[:8]
    new_arrivals = Product.objects.filter(is_active=True, is_new_arrival=True)[:8]
    collections = Collection.objects.filter(is_active=True)[:6]
    fragrance_families = FragranceFamily.objects.all()[:10]
    occasions = Occasion.objects.all()[:10]
    featured = Product.objects.filter(is_active=True, is_featured=True)[:4]
    sections = HomepageSection.objects.filter(is_active=True)
    newsletter_form = NewsletterForm()

    context = build_luxury_page_context()
    context.update({
        'banners': banners,
        'best_sellers': best_sellers,
        'new_arrivals': new_arrivals,
        'collections': collections,
        'fragrance_families': fragrance_families,
        'occasions': occasions,
        'featured': featured,
        'sections': sections,
        'newsletter_form': newsletter_form,
    })
    return render(request, 'core/home.html', context)


def about(request):
    site = SiteSettings.get()
    return render(request, 'core/about.html', {'site': site})


def contact(request):
    site = SiteSettings.get()
    form = ContactForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        ContactEnquiry.objects.create(
            name=form.cleaned_data['name'],
            email=form.cleaned_data['email'],
            phone=form.cleaned_data.get('phone', ''),
            subject=form.cleaned_data['subject'],
            message=form.cleaned_data['message'],
            enquiry_type=form.cleaned_data.get('enquiry_type', 'general'),
        )
        send_mail(
            subject=f'Contact: {form.cleaned_data["subject"]}',
            message=(
                f'From: {form.cleaned_data["name"]} ({form.cleaned_data["email"]})\n'
                f'Phone: {form.cleaned_data.get("phone", "N/A")}\n'
                f'Type: {form.cleaned_data.get("enquiry_type", "general")}\n\n'
                f'{form.cleaned_data["message"]}'
            ),
            from_email=settings.DEFAULT_FROM_EMAIL or form.cleaned_data['email'],
            recipient_list=[site.email or 'admin@elvassora.com'],
            fail_silently=True,
        )
        messages.success(request, 'Thank you! We will get back to you soon.')
        form = ContactForm()
    return render(request, 'core/contact.html', {'form': form, 'site': site})


def faq(request):
    faqs = FAQ.objects.filter(is_active=True)
    category_labels = dict(FAQ.CATEGORY_CHOICES)
    categories = []
    for key, label in FAQ.CATEGORY_CHOICES:
        count = sum(1 for f in faqs if f.category == key)
        if count:
            categories.append({'key': key, 'label': label, 'count': count})
    return render(request, 'core/faq.html', {
        'faqs': faqs,
        'faq_categories': categories,
        'category_labels': category_labels,
    })


def legal_page(request, page_type):
    page = get_object_or_404(LegalPage, page_type=page_type)
    return render(request, 'core/legal.html', {'page': page})


def newsletter_subscribe(request):
    if request.method == 'POST':
        form = NewsletterForm(request.POST)
        if form.is_valid():
            email = form.cleaned_data['email']
            NewsletterSubscriber.objects.get_or_create(email=email)
            messages.success(request, 'Successfully subscribed to our newsletter!')
        else:
            messages.error(request, 'Please enter a valid email address.')
    return redirect(request.META.get('HTTP_REFERER', 'core:home'))


def sitemap_xml(request):
    from blog.models import BlogPost
    site = SiteSettings.get()
    base = request.build_absolute_uri('/').rstrip('/')
    urls = [
        {'loc': f'{base}/', 'priority': '1.0'},
        {'loc': f'{base}/about/', 'priority': '0.6'},
        {'loc': f'{base}/contact/', 'priority': '0.5'},
        {'loc': f'{base}/blog/', 'priority': '0.7'},
    ]
    for p in Product.objects.filter(is_active=True).only('slug', 'updated_at'):
        urls.append({
            'loc': f'{base}{p.get_absolute_url()}',
            'lastmod': p.updated_at.date().isoformat(),
            'priority': '0.8',
        })
    for c in Collection.objects.filter(is_active=True).only('slug'):
        urls.append({'loc': f'{base}{c.get_absolute_url()}', 'priority': '0.6'})
    for post in BlogPost.objects.filter(is_published=True).only('slug', 'updated_at'):
        urls.append({
            'loc': f'{base}{post.get_absolute_url()}',
            'lastmod': post.updated_at.date().isoformat(),
            'priority': '0.6',
        })
    lines = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">',
    ]
    for u in urls:
        lines.append('<url>')
        lines.append(f'<loc>{u["loc"]}</loc>')
        if u.get('lastmod'):
            lines.append(f'<lastmod>{u["lastmod"]}</lastmod>')
        lines.append(f'<priority>{u["priority"]}</priority>')
        lines.append('</url>')
    lines.append('</urlset>')
    return HttpResponse('\n'.join(lines), content_type='application/xml')
