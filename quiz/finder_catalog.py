"""Build Perfume Finder catalog from Elvessora signature products."""

from django.templatetags.static import static
from django.urls import reverse

from products.fragrance_utils import SIGNATURE_SKUS, resolve_product_image_url
from products.models import GiftSet, Product

# Extra metadata for matching (seasons, intensity, extended families)
FINDER_META = {
    'ELV-MOON-001': {
        'seasons': ['spring', 'autumn', 'all'],
        'intensity': 'moderate',
        'scent_families': ['floral', 'sweet', 'oriental'],
        'match_reasons': {
            'gender': 'A romantic floral crafted for feminine elegance.',
            'occasion': 'Perfect for date nights and special evenings.',
            'season': 'Blooms beautifully in spring and autumn evenings.',
            'scent': 'Soft moonflower and white rose create a dreamy floral aura.',
            'intensity': 'Moderate projection with a refined, lasting trail.',
            'budget': 'Premium evening floral at accessible luxury pricing.',
        },
    },
    'ELV-SECRET-002': {
        'seasons': ['autumn', 'winter', 'all'],
        'intensity': 'strong',
        'scent_families': ['floral', 'fruity', 'sweet', 'oriental'],
        'match_reasons': {
            'gender': 'A sensual floral-fruity signature for her.',
            'occasion': 'Made for romance, parties, and unforgettable nights.',
            'season': 'Rich berry and rose notes shine in cooler months.',
            'scent': 'Red berries and peony deliver irresistible sweetness.',
            'intensity': 'Strong, long-lasting presence that turns heads.',
            'budget': 'Our most luxurious signature — worth every dirham.',
        },
    },
    'ELV-AMBER-003': {
        'seasons': ['autumn', 'winter'],
        'intensity': 'strong',
        'scent_families': ['oriental', 'floral', 'spicy', 'sweet'],
        'match_reasons': {
            'gender': 'Warm amber elegance suited to all genders.',
            'occasion': 'Ideal for office sophistication and special occasions.',
            'season': 'Golden amber warmth for autumn and winter.',
            'scent': 'Saffron, rose petals, and amber create opulent depth.',
            'intensity': 'Strong and enveloping with 10+ hour longevity.',
            'budget': 'Mid-luxury oriental at exceptional value.',
        },
    },
    'ELV-ENCHANT-004': {
        'seasons': ['spring', 'summer', 'all'],
        'intensity': 'light',
        'scent_families': ['floral', 'fruity', 'sweet', 'fresh'],
        'match_reasons': {
            'gender': 'Radiant and feminine with modern charm.',
            'occasion': 'Lovely for daily wear, daytime dates, and gifting.',
            'season': 'Fresh apple and jasmine bloom in spring and summer.',
            'scent': 'Enchanting apple-jasmine-vanilla harmony.',
            'intensity': 'Light to moderate — elegant without overpowering.',
            'budget': 'Premium floral-fruity within a refined budget.',
        },
    },
    'ELV-DIVINE-005': {
        'seasons': ['spring', 'summer', 'all'],
        'intensity': 'moderate',
        'scent_families': ['fresh', 'floral', 'fruity', 'aquatic'],
        'match_reasons': {
            'gender': 'A versatile fresh-floral for everyone.',
            'occasion': 'Perfect for daily wear, office, and summer days.',
            'season': 'Watermelon and orange blossom feel sun-kissed and airy.',
            'scent': 'Celestial fresh notes with a clean musky finish.',
            'intensity': 'Moderate freshness that lasts through the day.',
            'budget': 'Our most accessible signature — smart everyday luxury.',
        },
    },
}

GIFT_SET_META = {
    'discovery': {
        'seasons': ['all'],
        'intensity': 'moderate',
        'scent_families': ['floral', 'fresh', 'fruity', 'oriental'],
        'gender': 'unisex',
        'occasions': ['gift', 'daily', 'special'],
        'notes': 'Curated miniatures of our signature line',
        'match_reasons': {
            'default': 'Explore multiple Elvessora signatures in one luxury set.',
        },
    },
    'duo': {
        'seasons': ['all'],
        'intensity': 'moderate',
        'scent_families': ['floral', 'oriental', 'sweet'],
        'gender': 'unisex',
        'occasions': ['gift', 'date', 'wedding', 'special'],
        'notes': 'Two complementary signature fragrances',
        'match_reasons': {
            'default': 'A paired gift of our most-loved Elvessora scents.',
        },
    },
}


def _short_name(name):
    for prefix in ('Elvessora - ', 'Elvessora '):
        if name.startswith(prefix):
            return name[len(prefix):]
    return name


def _product_entry(product):
    meta = FINDER_META.get(product.sku, {})
    families = list(product.fragrance_families.values_list('name', flat=True))
    occasions = list(product.occasions.values_list('name', flat=True))
    notes = ', '.join(filter(None, [product.top_notes, product.heart_notes, product.base_notes]))
    price = float(product.offer_price or product.regular_price)

    return {
        'id': product.id,
        'sku': product.sku,
        'slug': product.slug,
        'name': _short_name(product.name),
        'full_name': product.name,
        'price': price,
        'price_display': f'AED {int(price):,}',
        'gender': product.gender,
        'occasions': occasions + ['gift'],
        'seasons': meta.get('seasons', ['all']),
        'scent_families': meta.get('scent_families', families),
        'intensity': meta.get('intensity', 'moderate'),
        'notes': notes,
        'description': product.description,
        'image': resolve_product_image_url(product),
        'url': reverse('products:product_detail', args=[product.slug]),
        'wishlist_url': reverse('accounts:wishlist_toggle', args=[product.id]),
        'type': 'product',
        'match_reasons': meta.get('match_reasons', {}),
    }


def _gift_entry(gift_set, slug_hint):
    meta = GIFT_SET_META.get(slug_hint, GIFT_SET_META['discovery'])
    price = float(gift_set.current_price)
    image = gift_set.image.url if gift_set.image else static('images/products/elvessora-moon-blossom.png')

    return {
        'id': f'gift-{gift_set.id}',
        'sku': f'GIFT-{gift_set.id}',
        'slug': gift_set.slug,
        'name': gift_set.name,
        'full_name': gift_set.name,
        'price': price,
        'price_display': f'AED {int(price):,}',
        'gender': meta['gender'],
        'occasions': meta['occasions'],
        'seasons': meta['seasons'],
        'scent_families': meta['scent_families'],
        'intensity': meta['intensity'],
        'notes': meta['notes'],
        'description': gift_set.description or 'A curated Elvessora luxury gift.',
        'image': image,
        'url': reverse('products:gift_set_detail', args=[gift_set.slug]),
        'wishlist_url': '',
        'type': 'gift',
        'match_reasons': meta['match_reasons'],
    }


def build_finder_catalog():
    """Return list of perfume dicts for the interactive finder."""
    catalog = []

    products = (
        Product.objects.filter(is_active=True, sku__in=SIGNATURE_SKUS)
        .prefetch_related('fragrance_families', 'occasions')
        .order_by('sku')
    )
    for product in products:
        catalog.append(_product_entry(product))

    gift_sets = GiftSet.objects.filter(is_active=True)[:3]
    for gift_set in gift_sets:
        hint = 'duo' if 'duo' in gift_set.slug else 'discovery'
        catalog.append(_gift_entry(gift_set, hint))

    # Pad catalog toward 8 entries with logical aliases if fewer gift sets exist
    if len(catalog) < 8 and products.exists():
        extras = [
            ('Elvessora Hair & Body Mist — FA', 'ELV-ENCHANT-004', ['daily', 'gift', 'summer'], ['fresh', 'floral', 'fruity']),
            ('Elvessora 1991 Edition', 'ELV-MOON-001', ['date', 'night', 'party'], ['oriental', 'floral', 'woody']),
            ('Elvessora Summer Bloom', 'ELV-DIVINE-005', ['daily', 'office', 'summer'], ['fresh', 'aquatic', 'citrus']),
        ]
        base_by_sku = {p.sku: p for p in products}
        for idx, (label, sku, occasions, families) in enumerate(extras):
            if len(catalog) >= 8:
                break
            base = base_by_sku.get(sku)
            if not base:
                continue
            entry = _product_entry(base)
            entry['id'] = f'variant-{idx + 1}'
            entry['name'] = label.replace('Elvessora ', '')
            entry['full_name'] = label
            entry['occasions'] = list(set(entry['occasions'] + occasions))
            entry['scent_families'] = list(set(entry['scent_families'] + families))
            catalog.append(entry)

    return catalog
