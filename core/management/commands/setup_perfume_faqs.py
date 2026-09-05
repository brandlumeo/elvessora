from django.core.management.base import BaseCommand
from core.models import FAQ


class Command(BaseCommand):
    help = 'Populates the site-wide FAQ page with the perfume FAQ content'

    def handle(self, *args, **kwargs):
        faqs_data = [
            ('Are your perfumes original?',
             'Yes, all our perfumes are sourced from trusted suppliers.',
             'products_ingredients'),
            ('How long does the fragrance last?',
             'Longevity varies depending on the fragrance, skin type, and environment. '
             'Our perfumes are selected for long-lasting performance.',
             'fragrance_guide'),
            ('What is the perfume size?',
             'Our perfumes are available in 50 ml.',
             'products_ingredients'),
            ('Are the perfumes suitable for men and women?',
             'Yes. We offer fragrances for men, women, and unisex preferences.',
             'products_ingredients'),
            ('How should I store my perfume?',
             'Keep it in a cool, dry place away from direct sunlight and heat.',
             'fragrance_guide'),
            ('Can I return or exchange a perfume?',
             'For hygiene and safety reasons, opened or used perfumes may not be eligible for '
             'return or exchange. Please check our return policy before purchasing.',
             'returns_refunds'),
            ('How can I choose the right fragrance?',
             'You can choose based on fragrance families such as floral, fruity, woody, '
             'oriental, fresh, and sweet.',
             'fragrance_guide'),
            ('Do you offer gift packaging?',
             'Yes, gift packaging can be available depending on the product.',
             'orders_shipping'),
            ('How can I place an order?',
             'Orders can be placed through our website or our official social media channels.',
             'orders_shipping'),
            ('Do you deliver across the UAE?',
             'Yes, UAE delivery is available. Delivery charges and times may vary by location.',
             'orders_shipping'),
            ('How can I contact you for more information?',
             'Contact us through our official website, WhatsApp, or social media for assistance.',
             'account_support'),
        ]

        for order, (question, answer, category) in enumerate(faqs_data, start=1):
            faq, created = FAQ.objects.update_or_create(
                question=question,
                defaults={
                    'answer': answer,
                    'category': category,
                    'order': order,
                    'is_active': True,
                },
            )
            action = 'Created' if created else 'Updated'
            self.stdout.write(self.style.SUCCESS(f'{action}: {question}'))

        self.stdout.write(self.style.SUCCESS(f'\nDone — {len(faqs_data)} FAQs are set up.'))
