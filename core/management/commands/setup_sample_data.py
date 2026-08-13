from decimal import Decimal
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import SiteSettings, FAQ, LegalPage
from products.models import (
    Category, Collection, FragranceFamily, Occasion,
    Product, ProductVariant, GiftSet,
)
from products.management.commands.load_elvessora_fragrances import upsert_elvessora_fragrances
from orders.models import Coupon
from marketing.models import Banner, HomepageSection, PromoPopup


class Command(BaseCommand):
    help = 'Populate the database with sample Elvessora perfume store data'

    def handle(self, *args, **options):
        self.stdout.write('Setting up Elvessora sample data...')

        SiteSettings.objects.update_or_create(pk=1, defaults={
            'brand_name': 'Elvessora',
            'tagline': 'General Trading & E-commerce — Dubai, UAE',
            'brand_story': (
                'At Elvessora, we are committed to delivering excellence in every order and every partnership. '
                'Whether you are sourcing business essentials, technology products, medical consumables, office supplies, '
                'or premium lifestyle products, our goal is to provide reliable solutions that help our customers succeed.'
            ),
            'about_company': (
                'Elvessora General Trading LLC is a Dubai-based trading company delivering premium products '
                'with luxury and trust. We serve retail and corporate clients across the UAE with quality, '
                'elegance, and reliability.'
            ),
            'business_address': 'ELVESSORA GENERAL TRADING LLC\nDubai, United Arab Emirates',
            'email': 'info@elvessora.ae',
            'phone': '+971 50 872 8042',
            'whatsapp_number': '971508728042',
            'instagram_url': 'https://www.instagram.com/elvessoraperfumes/',
            'facebook_url': 'https://www.facebook.com/profile.php?id=61592052402320',
            'twitter_url': 'https://x.com/elvessora',
            'youtube_url': 'https://youtube.com/elvassora',
            'pinterest_url': 'https://pinterest.com/elvassora',
            'free_shipping_threshold': Decimal('1999'),
            'default_shipping_charge': Decimal('99'),
            'tax_rate': Decimal('18'),
            'courier_partner': 'BlueDart Express',
        })

        admin, created = User.objects.get_or_create(username='admin', defaults={
            'email': 'admin@elvassora.com',
            'is_staff': True,
            'is_superuser': True,
        })
        if created:
            admin.set_password('admin123')
            admin.save()
            self.stdout.write(self.style.SUCCESS('Admin user created: admin / admin123'))

        category, _ = Category.objects.get_or_create(name='Perfumes', defaults={
            'description': 'Luxury perfume collection',
        })

        collections_data = ['Elvessora Signature', 'Oriental Nights', 'Fresh Bloom', 'Royal Oud']
        collections = {}
        for name in collections_data:
            collections[name], _ = Collection.objects.get_or_create(name=name)

        for choice_value, _ in FragranceFamily.FAMILIES:
            FragranceFamily.objects.get_or_create(name=choice_value)

        for choice_value, _ in Occasion.OCCASIONS:
            Occasion.objects.get_or_create(name=choice_value)

        upsert_elvessora_fragrances(stdout=self.stdout)

        Coupon.objects.get_or_create(code='WELCOME10', defaults={
            'description': '10% off your first order',
            'discount_type': 'percent',
            'discount_value': Decimal('10'),
            'min_order_amount': Decimal('999'),
            'max_uses': 1000,
        })

        Banner.objects.get_or_create(title='Discover Your Signature Scent', defaults={
            'subtitle': 'Explore our curated collection of luxury fragrances',
            'position': 'hero',
            'link_url': '/shop/',
            'button_text': 'Shop Now',
            'is_active': True,
        })

        for section_type, title in [
            ('best_sellers', 'Best Sellers'),
            ('new_arrivals', 'New Arrivals'),
            ('collections', 'Collections'),
            ('gift_sets', 'Gift Sets'),
        ]:
            HomepageSection.objects.get_or_create(section_type=section_type, defaults={'title': title})

        PromoPopup.objects.get_or_create(title='Welcome to Elvessora!', defaults={
            'content': 'Get 10% off your first order with code WELCOME10',
            'coupon_code': 'WELCOME10',
            'is_active': True,
        })

        FAQ.objects.get_or_create(question='How long does shipping take?', defaults={
            'answer': 'Standard delivery takes 3-5 business days across India.',
            'order': 1,
        })
        FAQ.objects.get_or_create(question='Do you offer Cash on Delivery?', defaults={
            'answer': 'Yes, COD is available on eligible orders across India. Online payment via Card, UPI, and Net Banking is also supported.',
            'order': 3,
        })
        FAQ.objects.get_or_create(question='What is the GST rate?', defaults={
            'answer': '18% GST is applied on all orders as per Indian tax regulations.',
            'order': 4,
        })

        products = list(Product.objects.all())
        if products:
            gift1, _ = GiftSet.objects.get_or_create(name='Luxury Duo Gift Box', defaults={
                'gift_type': 'box',
                'description': 'Premium gift box with two bestselling Elvessora fragrances. Includes custom gift wrapping and personalized message card.',
                'regular_price': Decimal('7999'),
                'offer_price': Decimal('6499'),
                'custom_wrapping_available': True,
                'personalized_message_available': True,
                'stock_quantity': 15,
            })
            if gift1.products.count() == 0 and len(products) >= 2:
                gift1.products.set(products[:2])

            gift2, _ = GiftSet.objects.get_or_create(name='Discovery Mini Collection', defaults={
                'gift_type': 'mini',
                'description': 'Set of 4 miniature perfumes — perfect for gifting or discovering new favourites.',
                'regular_price': Decimal('3499'),
                'offer_price': Decimal('2999'),
                'custom_wrapping_available': True,
                'personalized_message_available': True,
                'stock_quantity': 20,
            })
            if gift2.products.count() == 0 and len(products) >= 4:
                gift2.products.set(products[:4])

        for page_type, title, content in [
            ('privacy', 'Privacy Policy',
             'Elvessora respects your privacy. We collect personal information such as name, email, phone, and address solely to process orders and improve your shopping experience. We do not sell your data to third parties.'),
            ('terms', 'Terms & Conditions',
             'By accessing and using the Elvessora website, you agree to comply with our terms. All products are subject to availability. Prices are inclusive of applicable taxes unless stated otherwise.'),
            ('shipping', 'Shipping Policy',
             'We deliver across India via our courier partner BlueDart Express. Standard shipping charge is ₹99. Free shipping on orders above ₹1999. Estimated delivery: 3-5 business days.'),
            ('returns', 'Return & Refund Policy',
             'Unopened and unused products may be returned within 7 days of delivery. Refunds are processed within 5-7 business days after inspection. Opened perfumes cannot be returned due to hygiene reasons.'),
            ('cancellation', 'Cancellation Policy',
             'Orders can be cancelled before they are shipped. Once shipped, cancellation is not possible — please refer to our Return Policy.'),
            ('cookies', 'Cookie Policy',
             'We use cookies to remember your preferences, keep items in your cart, and analyse site traffic. You can disable cookies in your browser settings.'),
        ]:
            LegalPage.objects.get_or_create(page_type=page_type, defaults={'title': title, 'content': content})

        self.stdout.write(self.style.SUCCESS('Sample data loaded successfully!'))
