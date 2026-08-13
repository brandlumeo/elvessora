from decimal import Decimal

from products.fragrance_utils import SIGNATURE_SKUS
from products.models import Product

BUDGET_RANGES = {
    'low': (Decimal('0'), Decimal('99.99')),
    'mid': (Decimal('100'), Decimal('124.99')),
    'high': (Decimal('125'), Decimal('149.99')),
    'premium': (Decimal('150'), Decimal('999999')),
}

DAY_OCCASIONS = {'daily', 'office', 'day', 'summer'}
NIGHT_OCCASIONS = {'date', 'party', 'night', 'wedding'}


def _product_price(product):
    return product.offer_price if product.offer_price else product.regular_price


def score_product(product, data):
    """Score a signature fragrance against quiz answers (higher = better match)."""
    score = 0
    family_names = set(product.fragrance_families.values_list('name', flat=True))
    occasion_names = set(product.occasions.values_list('name', flat=True))

    if data['gender'] != 'any':
        if product.gender == data['gender']:
            score += 4
    else:
        score += 1

    if data['fragrance_family'] in family_names:
        score += 6

    if data['occasion'] in occasion_names:
        score += 5

    price = _product_price(product)
    low, high = BUDGET_RANGES[data['budget']]
    if low <= price <= high:
        score += 3

    if data['time_of_use'] == 'day':
        if occasion_names & DAY_OCCASIONS:
            score += 2
    elif data['time_of_use'] == 'night':
        if occasion_names & NIGHT_OCCASIONS:
            score += 2
    else:
        score += 1

    if data.get('preferred_notes'):
        all_notes = ' '.join(
            filter(None, [product.top_notes, product.heart_notes, product.base_notes])
        ).lower()
        for note in data['preferred_notes'].split(','):
            note = note.strip().lower()
            if note and note in all_notes:
                score += 3

    if product.is_best_seller:
        score += 1

    return score


def recommend_fragrances(data, limit=5):
    """Return best-matching Elvessora signature fragrances for quiz answers."""
    products = list(
        Product.objects.filter(is_active=True, sku__in=SIGNATURE_SKUS)
        .prefetch_related('fragrance_families', 'occasions')
    )
    if not products:
        return []

    scored = [(product, score_product(product, data)) for product in products]
    scored.sort(key=lambda item: (-item[1], -int(item[0].is_best_seller), item[0].name))

    matches = [product for product, points in scored if points > 0]
    if matches:
        return matches[:limit]

    return [product for product, _ in scored[:limit]]
