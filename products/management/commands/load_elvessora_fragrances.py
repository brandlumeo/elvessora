from decimal import Decimal
from pathlib import Path

from django.conf import settings
from django.core.files import File
from django.core.management.base import BaseCommand
from django.utils.text import slugify

from products.fragrance_utils import PRODUCT_STATIC_IMAGES
from products.models import (
    Category,
    Collection,
    FragranceFamily,
    Occasion,
    Product,
    ProductImage,
    ProductVariant,
)

ELVESSORA_FRAGRANCES = [
    {
        'name': 'Elvessora - Moon Blossom',
        'sku': 'ELV-MOON-001',
        'description': (
            'A luminous night-floral fragrance that captures the quiet elegance of moonlit petals. '
            'Soft, romantic, and beautifully refined — crafted for evenings that linger in memory.'
        ),
        'top_notes': 'Bergamot, Pear, Pink Pepper',
        'heart_notes': 'Moonflower, White Rose, Peony',
        'base_notes': 'White Musk, Soft Amber, Cedarwood',
        'main_accords': 'floral:90,musky:78,powdery:72,fresh:65',
        'concentration': 'edp',
        'gender': 'women',
        'regular_price': Decimal('90'),
        'offer_price': None,
        'families': ['floral', 'musk'],
        'occasions': ['date', 'night', 'special'],
        'collection': 'Elvessora Signature',
        'best_seller': True,
        'new': False,
        'featured': True,
    },
    {
        'name': 'Elvessora - Secret Romance',
        'sku': 'ELV-SECRET-002',
        'description': (
            'Secret of Romance — an intimate floral-fruity Elvessora fragrance woven for whispered moments '
            'and timeless romance. Elegant, sensual, and unmistakably luxury.'
        ),
        'top_notes': 'Red Berries, Mandarin, Bergamot',
        'heart_notes': 'Rose, Peony, Violet',
        'base_notes': 'Vanilla, Patchouli, Musk',
        'main_accords': 'floral:88,fruity:82,vanilla:75,musky:68,sweet:65',
        'concentration': 'edp',
        'gender': 'women',
        'regular_price': Decimal('145'),
        'offer_price': None,
        'families': ['floral', 'fruity'],
        'occasions': ['date', 'party', 'night'],
        'collection': 'Elvessora Signature',
        'best_seller': True,
        'new': True,
        'featured': True,
    },
    {
        'name': 'Elvessora - Amber Petals',
        'sku': 'ELV-AMBER-003',
        'description': (
            'Warm golden amber meets delicate floral petals in a luxurious oriental blend. '
            'Rich, enveloping, and sophisticated — a signature of quiet opulence.'
        ),
        'top_notes': 'Saffron, Bergamot, Pink Pepper',
        'heart_notes': 'Rose Petals, Jasmine, Orange Blossom',
        'base_notes': 'Amber, Vanilla, Benzoin',
        'main_accords': 'amber:92,oriental:85,floral:78,vanilla:72,warm spicy:60',
        'concentration': 'edp',
        'gender': 'unisex',
        'regular_price': Decimal('115'),
        'offer_price': None,
        'families': ['oriental', 'floral'],
        'occasions': ['office', 'special', 'winter'],
        'collection': 'Elvessora Signature',
        'best_seller': True,
        'new': False,
        'featured': True,
    },
    {
        'name': 'Elvessora - Enchanté Bloom',
        'sku': 'ELV-ENCHANT-004',
        'description': (
            'A fresh, enchanting floral with the crisp sweetness of apple and the elegance of jasmine, '
            'resting on a smooth vanilla base. Radiant, modern, and irresistibly feminine.'
        ),
        'top_notes': 'Sweet Apple',
        'heart_notes': 'Jasmine Flowers',
        'base_notes': 'Vanilla',
        'main_accords': 'fruity:85,floral:80,vanilla:78,sweet:75',
        'concentration': 'edp',
        'gender': 'women',
        'regular_price': Decimal('125'),
        'offer_price': None,
        'families': ['floral', 'fruity'],
        'occasions': ['daily', 'day', 'date'],
        'collection': 'Elvessora Signature',
        'best_seller': True,
        'new': True,
        'featured': True,
    },
    {
        'name': 'Elvessora - Divine Aura',
        'sku': 'ELV-DIVINE-005',
        'description': (
            'A celestial fresh-floral fragrance opening with lavender, watermelon, and Sicilian orange, '
            'blooming into lily of the valley, jasmine, and lotus — grounded by white musk, ambroxan, and sandalwood.'
        ),
        'top_notes': 'Lavender, Watermelon, Sicilian Orange, Red Fruits',
        'heart_notes': 'Lily of the Valley, Jasmine, Lotus',
        'base_notes': 'White Musk, Ambroxan, Sandalwood',
        'main_accords': 'fresh:90,fruity:85,floral:82,aromatic:78,musky:72,woody:68',
        'concentration': 'edp',
        'gender': 'unisex',
        'regular_price': Decimal('85'),
        'offer_price': None,
        'families': ['fresh', 'floral', 'fruity'],
        'occasions': ['daily', 'office', 'summer', 'day'],
        'collection': 'Elvessora Signature',
        'best_seller': True,
        'new': True,
        'featured': True,
    },
]

SIGNATURE_SKUS = {p['sku'] for p in ELVESSORA_FRAGRANCES}


def attach_product_images(stdout=None):
    static_dir = settings.BASE_DIR / 'static' / 'images' / 'products'
    attached = 0

    for sku, static_rel in PRODUCT_STATIC_IMAGES.items():
        product = Product.objects.filter(sku=sku).first()
        if not product:
            continue

        filename = Path(static_rel).name
        src = static_dir / filename
        if not src.exists():
            if stdout:
                stdout.write(f'Missing image file: {src}')
            continue

        product.images.all().delete()
        with open(src, 'rb') as image_file:
            ProductImage.objects.create(
                product=product,
                image=File(image_file, name=filename),
                alt_text=product.name,
                is_primary=True,
                order=0,
            )
        attached += 1

    if stdout:
        stdout.write(f'Attached product images: {attached}')
    return attached


def upsert_elvessora_fragrances(stdout=None):
    category, _ = Category.objects.get_or_create(
        name='Perfumes',
        defaults={'description': 'Elvessora luxury perfume collection'},
    )

    collection, _ = Collection.objects.get_or_create(
        name='Elvessora Signature',
        defaults={'description': 'The flagship Elvessora fragrance collection — crafted for timeless luxury.'},
    )

    for choice_value, _ in FragranceFamily.FAMILIES:
        FragranceFamily.objects.get_or_create(name=choice_value)

    for choice_value, _ in Occasion.OCCASIONS:
        Occasion.objects.get_or_create(name=choice_value)

    created_count = 0
    updated_count = 0

    for pdata in ELVESSORA_FRAGRANCES:
        product, created = Product.objects.update_or_create(
            sku=pdata['sku'],
            defaults={
                'name': pdata['name'],
                'slug': slugify(pdata['name']),
                'category': category,
                'collection': collection,
                'description': pdata['description'],
                'top_notes': pdata['top_notes'],
                'heart_notes': pdata['heart_notes'],
                'base_notes': pdata['base_notes'],
                'main_accords': pdata.get('main_accords', ''),
                'concentration': pdata['concentration'],
                'gender': pdata['gender'],
                'regular_price': pdata['regular_price'],
                'offer_price': pdata['offer_price'],
                'is_best_seller': pdata['best_seller'],
                'is_new_arrival': pdata['new'],
                'is_featured': pdata['featured'],
                'is_active': True,
                'country_of_origin': 'UAE',
                'usage_instructions': 'Spray on pulse points — wrists, neck, and behind the ears. Do not rub.',
                'meta_description': (
                    f"{pdata['name']} — luxury EDP by Elvessora. "
                    f"Top: {pdata['top_notes']}. Heart: {pdata['heart_notes']}. Base: {pdata['base_notes']}."
                ),
            },
        )

        if created:
            created_count += 1
        else:
            updated_count += 1

        product.fragrance_families.clear()
        for fam in pdata['families']:
            family = FragranceFamily.objects.filter(name=fam).first()
            if family:
                product.fragrance_families.add(family)

        product.occasions.clear()
        for occ_name in pdata['occasions']:
            occasion = Occasion.objects.filter(name=occ_name).first()
            if occasion:
                product.occasions.add(occasion)

        for size, multiplier in [('50ml', Decimal('1')), ('100ml', Decimal('1.4'))]:
            base_price = pdata['regular_price'] * multiplier
            base_offer = pdata['offer_price'] * multiplier if pdata.get('offer_price') else None
            ProductVariant.objects.update_or_create(
                product=product,
                size=size,
                defaults={
                    'sku': f"{pdata['sku']}-{size}",
                    'price': base_price,
                    'offer_price': base_offer,
                    'stock_quantity': 30,
                },
            )

    # Deactivate old sample perfumes not in the signature line
    deactivated = Product.objects.exclude(sku__in=SIGNATURE_SKUS).update(is_active=False)

    if stdout:
        stdout.write(f'Created: {created_count}, Updated: {updated_count}, Deactivated old: {deactivated}')

    attach_product_images(stdout=stdout)
    return created_count, updated_count


class Command(BaseCommand):
    help = 'Load or update the Elvessora signature perfume collection (5 fragrances)'

    def handle(self, *args, **options):
        self.stdout.write('Loading Elvessora signature fragrances...')
        created, updated = upsert_elvessora_fragrances(stdout=self.stdout)
        self.stdout.write(self.style.SUCCESS(
            f'Elvessora fragrances ready — {created} created, {updated} updated.'
        ))
