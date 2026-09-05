from django.core.management.base import BaseCommand
from core.models import Country, ShippingProvider, ShippingZone, SiteSettings


class Command(BaseCommand):
    help = 'Sets up the UAE country record and a UAE shipping zone'

    def handle(self, *args, **kwargs):
        uae, created = Country.objects.update_or_create(
            code='AE',
            defaults={'name': 'United Arab Emirates', 'phone_code': '+971', 'is_active': True},
        )
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} country: {uae.name}'))

        provider, created = ShippingProvider.objects.update_or_create(
            name='Courier (TBD)',
            defaults={'tracking_url_template': '', 'is_active': True},
        )
        self.stdout.write(self.style.SUCCESS(
            f'{"Created" if created else "Updated"} shipping provider: {provider.name} '
            '(placeholder — update its name and tracking_url_template once a courier is chosen)'
        ))

        zone, created = ShippingZone.objects.update_or_create(
            name='United Arab Emirates',
            defaults={
                'flat_rate': 99.00,
                'free_shipping_threshold': 1999.00,
                'estimated_days': '3-5 business days',
                'provider': provider,
                'is_active': True,
            },
        )
        zone.countries.set([uae])
        self.stdout.write(self.style.SUCCESS(f'{"Created" if created else "Updated"} shipping zone: {zone.name}'))

        settings_obj = SiteSettings.get()
        if settings_obj.courier_partner == 'BlueDart Express':
            settings_obj.courier_partner = ''
            settings_obj.save(update_fields=['courier_partner'])
            self.stdout.write(self.style.WARNING(
                'Cleared SiteSettings.courier_partner (was "BlueDart Express" — an India-only courier, '
                'not usable for UAE deliveries). Set the real courier name once decided.'
            ))

        self.stdout.write(self.style.SUCCESS('\nDone — UAE shipping zone is set up.'))
