from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.db import transaction


# (keep_user_id, [delete_user_ids]) — determined from the production audit.
# In every case the kept account is the Google-linked one, so Google
# sign-in keeps working; deleted accounts' passwords are lost but can be
# re-added via "Forgot password?".
MERGE_PLAN = [
    (14, [15, 16]),   # brandlumeollp@gmail.com
    (3, [11]),        # asnaf1899@gmail.com
    (4, [10]),        # rabeehmk485@gmail.com  (id=10 has 1 order + 1 wishlist item)
    (7, [13]),        # athiract1@gmail.com
]


class Command(BaseCommand):
    help = 'Merges the audited duplicate-email accounts, reassigning orders/reviews/wishlist first'

    def add_arguments(self, parser):
        parser.add_argument('--apply', action='store_true',
                            help='Actually perform the merge. Without this flag it only prints the plan (dry run).')

    def handle(self, *args, **options):
        apply = options['apply']
        self.stdout.write(self.style.WARNING('DRY RUN — nothing will change. Re-run with --apply to commit.\n')
                          if not apply else self.style.WARNING('APPLYING merge...\n'))

        with transaction.atomic():
            for keep_id, remove_ids in MERGE_PLAN:
                try:
                    keep = User.objects.get(pk=keep_id)
                except User.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'Keep user id={keep_id} not found — skipping this group.'))
                    continue

                self.stdout.write(f'\nKeep: id={keep.id} {keep.username!r} <{keep.email}>')

                for rid in remove_ids:
                    try:
                        remove = User.objects.get(pk=rid)
                    except User.DoesNotExist:
                        self.stdout.write(self.style.ERROR(f'  Remove user id={rid} not found — skipping.'))
                        continue

                    orders = list(remove.orders.all())
                    reviews = list(remove.reviews.all())
                    wishes = list(remove.wishlist_items.all())

                    self.stdout.write(
                        f'  Remove: id={remove.id} {remove.username!r} — '
                        f'{len(orders)} order(s), {len(reviews)} review(s), {len(wishes)} wishlist item(s)'
                    )

                    if apply:
                        remove.orders.update(user=keep)
                        # reviews: skip a review for a product the kept user already reviewed
                        keep_reviewed = set(keep.reviews.values_list('product_id', flat=True))
                        for r in reviews:
                            if r.product_id in keep_reviewed:
                                r.delete()
                            else:
                                r.user = keep
                                r.save(update_fields=['user'])
                        # wishlist: skip a product the kept user already has (unique constraint)
                        keep_wished = set(keep.wishlist_items.values_list('product_id', flat=True))
                        for w in wishes:
                            if w.product_id in keep_wished:
                                w.delete()
                            else:
                                w.user = keep
                                w.save(update_fields=['user'])

                        remove.delete()  # CASCADE clears profile, known_logins, notifications
                        self.stdout.write(self.style.SUCCESS(f'    merged into id={keep.id} and deleted.'))

            if not apply:
                self.stdout.write(self.style.WARNING('\nDry run complete — no changes made.'))
                transaction.set_rollback(True)
            else:
                self.stdout.write(self.style.SUCCESS('\nMerge complete.'))
