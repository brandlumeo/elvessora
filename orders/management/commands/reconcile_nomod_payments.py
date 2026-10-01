"""Brings unpaid Nomod orders in line with Nomod.

Nomod has no redirect or webhook for a checkout that simply expires, and a
shopper can close the tab before being redirected back. Run this on a
schedule (e.g. every 15 minutes via cron) so those orders end up paid,
cancelled or expired instead of sitting in 'pending' forever:

    */15 * * * * cd /path/to/project && venv/bin/python manage.py reconcile_nomod_payments
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders import nomod
from orders.models import Order
from orders.views import _sync_nomod_order


class Command(BaseCommand):
    help = 'Re-checks pending Nomod orders against Nomod and applies their payment status.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--older-than', type=int, default=10,
            help='Only check orders created at least this many minutes ago (default 10).',
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

        counts = {}
        for order in orders:
            state = _sync_nomod_order(order)
            counts[state] = counts.get(state, 0) + 1

        summary = ', '.join(f'{state}: {n}' for state, n in sorted(counts.items())) or 'no pending orders'
        self.stdout.write(f'Nomod reconcile — {summary}')
