"""Brings unpaid Nomod orders in line with Nomod.

Nomod has no redirect or webhook for a checkout that's simply abandoned, and
in practice an unpaid checkout stays 'enabled' rather than turning
'expired'. A shopper can also close the tab before being redirected back.
Run this on a schedule (e.g. every 15 minutes via cron) so those orders end
up paid or cancelled instead of sitting in 'pending' forever:

    */15 * * * * cd /path/to/project && venv/bin/python manage.py reconcile_nomod_payments
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders import nomod
from orders.models import Order
from orders.views import _mark_order_unpaid, _sync_nomod_order


class Command(BaseCommand):
    help = 'Re-checks pending Nomod orders against Nomod and applies their payment status.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than', type=int, default=10,
            help='Only check orders created at least this many minutes ago (default 10).',
        )
        parser.add_argument(
            '--abandon-after', type=int, default=120,
            help='Cancel orders whose Nomod checkout is still unpaid after this many '
                 'minutes (default 120). A payment that lands later is still picked '
                 'up by the webhook or when the customer returns to the site.',
        )
        parser.add_argument(
            '--max-age-days', type=int, default=7,
            help='Ignore orders older than this many days (default 7).',
        )

    def handle(self, *args, **options):
        if not nomod.is_configured():
            self.stdout.write('NOMOD_API_KEY is not set; nothing to reconcile.')
            return

        now = timezone.now()
        orders = Order.objects.filter(
            payment_method='nomod',
            payment_status='pending',
            created_at__lte=now - timedelta(minutes=options['older_than']),
            created_at__gte=now - timedelta(days=options['max_age_days']),
        ).exclude(nomod_checkout_id='')

        abandon_before = now - timedelta(minutes=options['abandon_after'])
        counts = {}
        for order in orders:
            state = _sync_nomod_order(order)
            if state == 'pending' and order.created_at <= abandon_before:
                _mark_order_unpaid(order.pk, cancel=True)
                state = 'abandoned'
            counts[state] = counts.get(state, 0) + 1

        summary = ', '.join(f'{state}: {n}' for state, n in sorted(counts.items())) or 'no pending orders'
        self.stdout.write(f'Nomod reconcile — {summary}')
