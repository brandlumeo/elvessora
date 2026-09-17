from django.contrib.auth.models import Group, Permission, User
from django.core.management.base import BaseCommand, CommandError

GROUP_NAME = 'Store Staff'

# (app_label, model_name, [codename actions]) — actions from Django's default set:
# 'add', 'change', 'delete', 'view'
FULL_CRUD_MODELS = [
    # Orders & Coupons
    ('orders', 'coupon'),
    # Products & Inventory
    ('products', 'brand'),
    ('products', 'category'),
    ('products', 'collection'),
    ('products', 'fragrancefamily'),
    ('products', 'occasion'),
    ('products', 'product'),
    ('products', 'productimage'),
    ('products', 'productvideo'),
    ('products', 'productimage360'),
    ('products', 'giftset'),
    ('products', 'productfaq'),
    ('inventory', 'inventory'),
    # Customers & Reviews
    ('accounts', 'address'),
    ('reviews', 'review'),
    # Marketing & CMS
    ('marketing', 'newslettersubscriber'),
    ('marketing', 'banner'),
    ('marketing', 'homepagesection'),
    ('marketing', 'promopopup'),
    ('marketing', 'contactenquiry'),
    ('marketing', 'flashsale'),
    ('marketing', 'emailcampaign'),
    ('core', 'faq'),
    ('core', 'legalpage'),
    ('core', 'homepagehighlight'),
]

# View + change only — no add/delete (avoid accidental creation/loss of records
# that should only ever come from real orders, payments, or the singleton content row)
VIEW_CHANGE_MODELS = [
    ('orders', 'order'),
    ('orders', 'refund'),
    ('accounts', 'customer'),
    ('accounts', 'userprofile'),
    ('marketing', 'abandonedcartreminder'),
    ('core', 'homepagecontent'),
]

# View only — sensitive financial records
VIEW_ONLY_MODELS = [
    ('orders', 'payment'),
]


class Command(BaseCommand):
    help = 'Create/update the "Store Staff" group (Orders, Products, Customers, Marketing — no Settings/Reports) and optionally assign a user to it.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user', dest='username', default=None,
            help='Username to add to the group and mark as staff.',
        )

    def _permissions_for(self, app_label, model, actions):
        perms = []
        for action in actions:
            codename = f'{action}_{model}'
            try:
                perms.append(Permission.objects.get(content_type__app_label=app_label, codename=codename))
            except Permission.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'  skipped missing permission: {app_label}.{codename}'))
        return perms

    def handle(self, *args, **options):
        group, created = Group.objects.get_or_create(name=GROUP_NAME)
        self.stdout.write(('Created' if created else 'Updating') + f' group "{GROUP_NAME}"')

        all_perms = []
        for app_label, model in FULL_CRUD_MODELS:
            all_perms += self._permissions_for(app_label, model, ['add', 'change', 'delete', 'view'])
        for app_label, model in VIEW_CHANGE_MODELS:
            all_perms += self._permissions_for(app_label, model, ['change', 'view'])
        for app_label, model in VIEW_ONLY_MODELS:
            all_perms += self._permissions_for(app_label, model, ['view'])

        group.permissions.set(all_perms)
        self.stdout.write(self.style.SUCCESS(f'Assigned {len(all_perms)} permissions to "{GROUP_NAME}"'))

        username = options.get('username')
        if username:
            try:
                user = User.objects.get(username=username)
            except User.DoesNotExist:
                raise CommandError(f'No such user: {username}')
            user.is_staff = True
            user.save(update_fields=['is_staff'])
            user.groups.add(group)
            self.stdout.write(self.style.SUCCESS(f'Marked "{username}" as staff and added to "{GROUP_NAME}"'))
