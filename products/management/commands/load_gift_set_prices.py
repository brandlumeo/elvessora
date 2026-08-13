from decimal import Decimal

from django.core.management.base import BaseCommand

from products.models import GiftSet


GIFT_SET_PRICES = {
    'discovery-mini-collection': {
        'regular_price': Decimal('349'),
        'offer_price': Decimal('299'),
    },
    'luxury-duo-gift-box': {
        'regular_price': Decimal('249'),
        'offer_price': Decimal('219'),
    },
}


class Command(BaseCommand):
    help = 'Update gift set prices to AED amounts.'

    def handle(self, *args, **options):
        updated = 0
        for gift_set in GiftSet.objects.all():
            prices = GIFT_SET_PRICES.get(gift_set.slug)
            if not prices:
                name_key = gift_set.name.lower()
                if 'mini' in name_key or 'discovery' in name_key:
                    prices = GIFT_SET_PRICES['discovery-mini-collection']
                elif 'duo' in name_key:
                    prices = GIFT_SET_PRICES['luxury-duo-gift-box']

            if prices:
                gift_set.regular_price = prices['regular_price']
                gift_set.offer_price = prices['offer_price']
                gift_set.save(update_fields=['regular_price', 'offer_price'])
                updated += 1
                self.stdout.write(f'{gift_set.name}: AED {gift_set.current_price}')

        self.stdout.write(self.style.SUCCESS(f'Updated {updated} gift set(s).'))
