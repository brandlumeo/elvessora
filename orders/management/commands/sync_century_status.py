"""Brings Century Express orders in line with Century's tracking.

Century Express has no webhooks, so run this on a schedule (e.g. every 30
minutes via cron) to move orders to shipped / out for delivery / delivered
as the parcel travels. Customers get the usual status notifications.

    */30 * * * * cd /path/to/project && venv/bin/python manage.py sync_century_status
"""
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone

from orders import century
from orders.models import Order


class Command(BaseCommand):
    help = 'Fetches Century Express status for undelivered orders and applies it.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-age-days', type=int, default=30,
            help='Ignore orders older than this many days (default 30).',
        )

    def handle(self, *args, **options):
        if not century.is_configured():
            self.stderr.write('Century Express is not configured; nothing to do.')
            return
        orders = (
            Order.objects
            .filter(courier_name=century.COURIER_NAME,
                    created_at__gte=timezone.now() - timedelta(days=options['max_age_days']))
            .exclude(tracking_number='')
            .exclude(status__in=['delivered', 'cancelled', 'refunded'])
        )
        checked = failed = 0
        for order in orders:
            try:
                text = century.sync_order(order)
                checked += 1
                self.stdout.write(f'{order.order_number} ({order.tracking_number}): {text or "no status"} -> {order.status}')
            except century.CenturyError as exc:
                failed += 1
                self.stderr.write(f'{order.order_number}: {exc}')
        self.stdout.write(f'Checked {checked} order(s), {failed} failed.')
