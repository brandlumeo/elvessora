from django.db import migrations
from django.utils import timezone
from django.utils.text import slugify

CONTENT = """
<p>Choosing a fragrance is a more personal decision for men than the shelves at most stores let on. Where womenswear perfumery leans into a wide spectrum of florals and gourmands, men are often steered toward the same handful of "safe" woody-aromatic blends — leaving plenty of genuinely great options overlooked simply because they were never marketed as "for him."</p>

<p>At Elvessora, we don't split our line by gender. We build each fragrance around a mood, and let you decide who it belongs to. Here's how to think about it if you're shopping for a men's signature scent.</p>

<h2>Start with intensity, not just notes</h2>
<p>A fragrance that reads beautifully on paper can feel completely different on skin, and projection matters more day-to-day than the note list. For daily wear — the office, a meeting, a flight — look for something moderate that lasts without announcing itself from across the room. Save the boldest, warmest compositions for evenings.</p>

<figure>
    <img src="/media/products/ChatGPT_Image_Sep_9_2026_05_27_05_PM.png" alt="Elvessora Amber Petals">
    <figcaption>Amber Petals — warm, golden, and grounded enough to wear from desk to dinner.</figcaption>
</figure>

<h2>Amber and woody-fresh do the heavy lifting</h2>
<p><strong>Amber Petals</strong> is where we'd point most men first. It opens with saffron and bergamot, settles into rose and jasmine, and finishes on amber, vanilla, and benzoin — a warm, grounded profile that reads sophisticated without being heavy. It's built for autumn and winter, office to evening, and it's one of our two fully unisex fragrances, so it was designed to wear well on any skin.</p>

<p><strong>Divine Aura</strong> takes the opposite season. Lavender, watermelon, and Sicilian orange open it up, before white musk, ambroxan, and sandalwood settle it down — fresh enough for daily wear, clean enough for the office, and versatile enough to become a genuine everyday signature.</p>

<figure>
    <img src="/media/products/ChatGPT_Image_Sep_10_2026_09_35_42_AM.png" alt="Elvessora Divine Aura">
    <figcaption>Divine Aura's fresh-woody finish makes it an easy everyday pick.</figcaption>
</figure>

<h2>Match the fragrance to the occasion, not just the season</h2>
<ul>
    <li><strong>Office &amp; daily wear:</strong> Divine Aura — fresh, clean, never overpowering.</li>
    <li><strong>Evenings &amp; colder months:</strong> Amber Petals — warm, resinous, long-lasting.</li>
    <li><strong>Uncertain which suits you:</strong> take our Perfume Finder quiz — it factors in intensity, season, and occasion, not just "men's" or "women's" labels.</li>
</ul>

<p>The best men's fragrance is the one that actually matches how you live day to day — not the one with the boldest bottle on the shelf. Start with intensity and occasion, and the right notes tend to follow.</p>
""".strip()


def add_post(apps, schema_editor):
    BlogCategory = apps.get_model('blog', 'BlogCategory')
    BlogPost = apps.get_model('blog', 'BlogPost')
    Product = apps.get_model('products', 'Product')
    User = apps.get_model('auth', 'User')

    author = User.objects.filter(username='elvessora_editor').first()

    category, _ = BlogCategory.objects.get_or_create(
        slug='mens-fragrance',
        defaults={'name': 'Mens Fragrance', 'is_active': True},
    )

    title = "A Guide to Men's Fragrance: How to Choose Your Signature Scent"
    slug = slugify(title)
    if BlogPost.objects.filter(slug=slug).exists():
        return

    post = BlogPost.objects.create(
        title=title,
        slug=slug,
        category=category,
        author=author,
        excerpt=(
            "Forget the 'his' and 'hers' labels — here's how to actually choose a "
            "fragrance that fits how you live, from daily wear to evenings out."
        ),
        content=CONTENT,
        featured_image='products/ChatGPT_Image_Sep_9_2026_05_27_05_PM.png',
        reading_time=5,
        meta_title="Men's Fragrance Guide — How to Choose Your Signature Scent",
        meta_description=(
            "A practical guide to choosing a men's fragrance — intensity, "
            "occasion, and which Elvessora scents to start with."
        ),
        meta_keywords='Mens Fragrance, Signature Scent, Amber Petals, Divine Aura, perfume guide',
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
    BlogPost.objects.filter(
        slug='a-guide-to-mens-fragrance-how-to-choose-your-signature-scent'
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('blog', '0003_blogpost_meta_keywords'),
        ('products', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_post, remove_post),
    ]
