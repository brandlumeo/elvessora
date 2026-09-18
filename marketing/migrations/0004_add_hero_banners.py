from django.db import migrations

BANNERS = [
    {
        'title': 'Amber Petals — Warmth in a Bottle',
        'subtitle': 'Saffron, rose, and amber for a scent that lingers long after you leave the room.',
        'image': 'products/ChatGPT_Image_Sep_9_2026_05_27_05_PM.png',
        'link_url': '/product/elvessora-amber-petals/',
        'button_text': 'Shop Amber Petals',
        'order': 1,
    },
    {
        'title': 'Secret Romance',
        'subtitle': 'An intimate floral-fruity signature, made for unforgettable nights.',
        'image': 'products/ChatGPT_Image_Sep_9_2026_05_17_01_PM.png',
        'link_url': '/product/elvessora-secret-romance/',
        'button_text': 'Shop Secret Romance',
        'order': 2,
    },
    {
        'title': 'Gift the Art of Fragrance',
        'subtitle': 'Curated gift sets with custom wrapping and a personalized message, ready to send.',
        'image': 'products/ChatGPT_Image_Sep_9_2026_05_47_18_PM.png',
        'link_url': '/gift-sets/',
        'button_text': 'Explore Gift Sets',
        'order': 3,
    },
]


def add_banners(apps, schema_editor):
    Banner = apps.get_model('marketing', 'Banner')
    for data in BANNERS:
        Banner.objects.get_or_create(
            title=data['title'],
            position='hero',
            defaults={
                'subtitle': data['subtitle'],
                'image': data['image'],
                'link_url': data['link_url'],
                'button_text': data['button_text'],
                'order': data['order'],
                'is_active': True,
            },
        )


def remove_banners(apps, schema_editor):
    Banner = apps.get_model('marketing', 'Banner')
    Banner.objects.filter(
        position='hero',
        title__in=[b['title'] for b in BANNERS],
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('marketing', '0003_admin_phase2'),
    ]

    operations = [
        migrations.RunPython(add_banners, remove_banners),
    ]
