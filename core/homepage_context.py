from django.db.models import Case, IntegerField, When

from core.models import HomePageContent, HomePageHighlight
from products.fragrance_utils import SIGNATURE_SKUS
from products.models import Collection, FragranceFamily, GiftSet, Product
from quiz.finder_catalog import build_finder_catalog


def build_luxury_page_context():
    """Shared context for homepage and collection landing."""
    best_sellers = Product.objects.filter(is_active=True, is_best_seller=True)[:8]
    signature_fragrances = list(
        Product.objects.filter(is_active=True, sku__in=SIGNATURE_SKUS)
        .prefetch_related('images', 'fragrance_families')
        .annotate(
            signature_order=Case(
                *[When(sku=sku, then=index) for index, sku in enumerate(SIGNATURE_SKUS)],
                output_field=IntegerField(),
            )
        )
        .order_by('signature_order')
    )
    spotlight = (
        Product.objects.filter(is_active=True, sku='ELV-MOON-001').first()
        or best_sellers.first()
        or (signature_fragrances[0] if signature_fragrances else None)
    )
    homepage = HomePageContent.get()

    return {
        'signature_fragrances': signature_fragrances,
        'spotlight': spotlight,
        'homepage': homepage,
        'finder_catalog': build_finder_catalog(),
        'fragrance_families': FragranceFamily.objects.all()[:10],
        'gift_sets': GiftSet.objects.filter(is_active=True).prefetch_related('products__images')[:4],
        'collections': Collection.objects.filter(is_active=True)[:6],
        'hero_features': HomePageHighlight.objects.filter(
            highlight_type='hero_feature', is_active=True,
        ),
        'ingredients': HomePageHighlight.objects.filter(
            highlight_type='ingredient', is_active=True,
        ),
        'value_props': HomePageHighlight.objects.filter(
            highlight_type='value_prop', is_active=True,
        ),
    }
