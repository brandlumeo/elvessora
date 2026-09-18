from django.db import migrations
from django.utils import timezone

CONTENT = """
<p>Buying perfume as a gift is nerve-wracking precisely because scent is so personal — get it wrong and it sits unused in a drawer. The good news: you don't need to know someone's exact taste to choose well. A few reliable rules get you most of the way there.</p>

<h2>When in doubt, go warm and universally loved</h2>
<p>Bold, polarizing scents are a gift for yourself, not the recipient. For someone you don't buy fragrance for regularly, lean toward warm, well-blended compositions that read as "expensive" and "safe" rather than experimental.</p>

<figure>
    <img src="/media/products/ChatGPT_Image_Sep_9_2026_05_27_05_PM.png" alt="Elvessora Amber Petals">
    <figcaption>Amber Petals — warm and universally flattering, a dependable gift pick.</figcaption>
</figure>

<p><strong>Amber Petals</strong> is our most reliable gift: saffron, rose, and amber make it feel luxurious without being difficult to wear, and it suits pretty much anyone on your list. <strong>Divine Aura</strong>, fresh and clean with watermelon and sandalwood, is the better call for someone who prefers lighter, everyday scents.</p>

<h2>Presentation matters as much as the perfume</h2>
<p>A gift that arrives well-wrapped reads as more thoughtful than one that doesn't — obvious, but easy to forget when you're buying online last-minute. Every order on Elvessora can include custom gift wrapping and a personalized message at checkout, so the presentation is taken care of without extra effort on your part.</p>

<h2>Gift sets solve the "which one?" problem</h2>
<p>If you genuinely can't decide, our <a href="/gift-sets/">curated gift sets</a> bundle multiple signature fragrances together, so your recipient gets to choose their favorite themselves rather than you guessing alone.</p>

<p>Last rule: check the return policy before you buy (ours allows returns on unopened gift sets), and you've covered every base a good fragrance gift needs.</p>
""".strip()


def add_post(apps, schema_editor):
    BlogCategory = apps.get_model('blog', 'BlogCategory')
    BlogPost = apps.get_model('blog', 'BlogPost')
    Product = apps.get_model('products', 'Product')
    User = apps.get_model('auth', 'User')

    author = User.objects.filter(username='elvessora_editor').first()

    category, _ = BlogCategory.objects.get_or_create(
        slug='gift-guides',
        defaults={'name': 'Gift Guides', 'is_active': True},
    )

    slug = 'perfume-gift-guide'
    if BlogPost.objects.filter(slug=slug).exists():
        return

    post = BlogPost.objects.create(
        title='How to Choose a Perfume Gift (Without Guessing Wrong)',
        slug=slug,
        category=category,
        author=author,
        excerpt=(
            "Scent is personal, but a few reliable rules make gifting fragrance "
            "far less risky — here's how to choose well every time."
        ),
        content=CONTENT,
        featured_image='products/ChatGPT_Image_Sep_9_2026_05_27_05_PM.png',
        reading_time=4,
        meta_title='How to Choose a Perfume Gift — Elvessora Gift Guide',
        meta_description=(
            'A practical guide to buying fragrance as a gift — which scents '
            'are safe bets, and how presentation and gift sets help.'
        ),
        meta_keywords='Gift Guides, Perfume Gift, Amber Petals, Divine Aura, Gift Sets',
        is_published=True,
        is_featured=False,
        published_at=timezone.now(),
    )

    related_skus = ['ELV-AMBER-003', 'ELV-DIVINE-005']
    related = list(Product.objects.filter(sku__in=related_skus))
    if related:
        post.related_products.set(related)


def remove_post(apps, schema_editor):
    BlogPost = apps.get_model('blog', 'BlogPost')
    BlogPost.objects.filter(slug='perfume-gift-guide').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0004_add_mens_fragrance_post'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_post, remove_post),
    ]
