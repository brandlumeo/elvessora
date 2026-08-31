from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.utils import timezone
from blog.models import BlogCategory, BlogTag, BlogPost, BlogFAQ
from products.models import Product

User = get_user_model()

class Command(BaseCommand):
    help = 'Populates the database with sample blog content'

    def handle(self, *args, **kwargs):
        # 1. Create User
        user, created = User.objects.get_or_create(
            username='elvessora_editor',
            defaults={
                'email': 'editorial@elvessora.com',
                'first_name': 'Elvessora',
                'last_name': 'Editorial Team',
                'is_staff': True,
            }
        )

        # 2. Create Categories
        categories_data = [
            'Perfume Guides', 'Fragrance Notes', 'Perfume Tips', 
            'Perfume Care', 'Lifestyle', 'Gift Guides', 
            'Mens Fragrance', 'Womens Fragrance', 'Unisex Fragrance', 'Elvessora Stories'
        ]
        categories = {}
        for cat_name in categories_data:
            cat, _ = BlogCategory.objects.get_or_create(name=cat_name)
            categories[cat_name] = cat

        # 3. Create Tags
        tags_data = ['Luxury', 'Longevity', 'Signature Scent', 'Oud', 'Storage']
        tags = {}
        for tag_name in tags_data:
            tag, _ = BlogTag.objects.get_or_create(name=tag_name)
            tags[tag_name] = tag

        # 4. Create Articles
        articles_data = [
            {
                'title': "The Art of Choosing Your Signature Scent",
                'category': 'Perfume Guides',
                'excerpt': "Discover how fragrance notes, personality, and occasion come together to help you find a scent that feels uniquely yours.",
                'content': """<p>Finding a signature scent is a deeply personal journey. Your fragrance is an invisible accessory that introduces you before you speak and lingers after you leave.</p>
                <h2>1. Understand the Fragrance Families</h2>
                <p>Before you begin sampling, it helps to know what you gravitate towards. Are you drawn to fresh, citrusy notes, or do you prefer deep, woody aromas like Oud and Sandalwood?</p>
                <blockquote>"A signature scent is the silent language of your soul."</blockquote>
                <h2>2. Test on Your Skin</h2>
                <p>Never judge a perfume entirely by smelling it on a paper strip. The true magic of a fragrance reveals itself when it mixes with your body's natural chemistry.</p>
                """,
                'is_featured': True,
                'reading_time': 6,
                'tags': ['Signature Scent', 'Luxury'],
                'faqs': [
                    {'q': 'How many signature scents should I have?', 'a': 'While having one is traditional, many build a "fragrance wardrobe" with 2-3 scents for different seasons.'},
                ]
            },
            {
                'title': "How to Make Your Perfume Last All Day",
                'category': 'Perfume Tips',
                'excerpt': "Discover simple techniques to improve fragrance longevity and make your signature scent stay with you throughout the day.",
                'content': """<p>We all want our favorite fragrance to last from morning until night. Here are the expert secrets to ensuring maximum longevity.</p>
                <h3>Moisturize First</h3>
                <p>Perfume evaporates quickly on dry skin. Applying an unscented lotion or matching body oil before spraying creates a base for the fragrance oils to cling to.</p>
                <h3>Target Pulse Points</h3>
                <p>Apply to your wrists, neck, inner elbows, and behind the knees. These areas generate body heat, which helps project the fragrance.</p>
                """,
                'is_featured': False,
                'reading_time': 5,
                'tags': ['Longevity', 'Perfume Tips'],
                'faqs': []
            },
            {
                'title': "Understanding Top, Middle & Base Notes",
                'category': 'Fragrance Notes',
                'excerpt': "A guide to the olfactory pyramid and how perfumes evolve on your skin over time.",
                'content': """<p>A fine fragrance tells a story in three parts. Understanding this structure will change how you experience perfume.</p>
                <h2>The Top Notes</h2>
                <p>The immediate scent. Usually fresh, light, and citrusy. They evaporate within the first 15-30 minutes.</p>
                <h2>The Heart (Middle) Notes</h2>
                <p>The core of the fragrance. Often floral or spicy, they emerge as the top notes fade and form the character of the scent.</p>
                <h2>The Base Notes</h2>
                <p>The foundation. Deep, rich notes like Oud, Amber, and Vanilla that linger for hours and anchor the entire composition.</p>
                """,
                'is_featured': False,
                'reading_time': 4,
                'tags': ['Luxury'],
                'faqs': []
            },
            {
                'title': "Oud, Amber & Musk: The Essence of Arabian Fragrance",
                'category': 'Fragrance Notes',
                'excerpt': "Explore the rich, captivating ingredients that have defined Middle Eastern perfumery for centuries.",
                'content': """<p>Middle Eastern perfumery is renowned for its depth, intensity, and opulent ingredients. The "holy trinity" of this olfactory world consists of Oud, Amber, and Musk.</p>
                <h3>The Liquid Gold: Oud</h3>
                <p>Derived from the agarwood tree, Oud is one of the most expensive raw materials in the world, prized for its complex woody, smoky, and slightly sweet profile.</p>
                """,
                'is_featured': False,
                'reading_time': 7,
                'tags': ['Oud', 'Luxury'],
                'faqs': []
            },
            {
                'title': "How to Store Your Perfume the Right Way",
                'category': 'Perfume Care',
                'excerpt': "Protect your investment. Learn the biggest mistakes people make when storing fine fragrances.",
                'content': """<p>Perfume is delicate. Exposure to the wrong elements can break down the oils and completely alter the scent.</p>
                <ul>
                    <li><strong>Keep it out of the bathroom:</strong> The fluctuating heat and humidity from showers will ruin your fragrance rapidly.</li>
                    <li><strong>Avoid direct sunlight:</strong> UV rays break down the chemical bonds. Store in a dark drawer or closet.</li>
                    <li><strong>Keep the original box:</strong> If possible, keeping the bottle in its box provides excellent protection against light.</li>
                </ul>
                """,
                'is_featured': False,
                'reading_time': 3,
                'tags': ['Storage'],
                'faqs': []
            },
            {
                'title': "The Perfect Fragrance for Every Occasion",
                'category': 'Lifestyle',
                'excerpt': "From boardrooms to date nights, learn how to select the right scent profile for the moment.",
                'content': """<p>Just as you wouldn't wear a tuxedo to the beach, certain fragrances are better suited for specific settings.</p>
                <h2>Office & Professional</h2>
                <p>Opt for clean, subtle, and fresh scents. You want to be discovered, not announced.</p>
                <h2>Evening & Date Night</h2>
                <p>This is where you can unleash deep, seductive notes like Vanilla, Amber, or a sophisticated Oud.</p>
                """,
                'is_featured': False,
                'reading_time': 5,
                'tags': [],
                'faqs': []
            },
            {
                'title': "How to Apply Perfume for Maximum Longevity",
                'category': 'Perfume Tips',
                'excerpt': "Stop rubbing your wrists together. Learn the proper ritual for applying luxury fragrances.",
                'content': """<p>Application is an art. Many of us have been taught incorrectly.</p>
                <blockquote>"Never rub your wrists together after spraying."</blockquote>
                <p>Friction heats up the skin and breaks down the delicate top notes of the perfume, rushing the evaporation process.</p>
                """,
                'is_featured': False,
                'reading_time': 4,
                'tags': ['Longevity'],
                'faqs': []
            },
            {
                'title': "The Story Behind Elvessora Divine Aura",
                'category': 'Elvessora Stories',
                'excerpt': "Take a behind-the-scenes look at the inspiration and craftsmanship that went into creating our signature scent.",
                'content': """<p>Creating Divine Aura was a journey that took our master perfumers over two years to perfect.</p>
                <p>The vision was to capture the golden hour in the desert—that brief, magical moment when the harsh sun softens, and the sand glows with an inner warmth.</p>
                <p>We achieved this by blending bright citrus top notes with a deeply resonant base of aged Oud and creamy Sandalwood.</p>
                """,
                'is_featured': False,
                'reading_time': 8,
                'tags': ['Luxury', 'Signature Scent'],
                'faqs': []
            }
        ]

        products = list(Product.objects.all()[:3])

        for data in articles_data:
            post, created = BlogPost.objects.get_or_create(
                title=data['title'],
                defaults={
                    'category': categories[data['category']],
                    'author': user,
                    'excerpt': data['excerpt'],
                    'content': data['content'],
                    'is_published': True,
                    'is_featured': data['is_featured'],
                    'reading_time': data['reading_time'],
                    'published_at': timezone.now(),
                }
            )
            
            if not created:
                post.category = categories[data['category']]
                post.excerpt = data['excerpt']
                post.content = data['content']
                post.is_published = True
                post.is_featured = data['is_featured']
                post.reading_time = data['reading_time']
                post.save()

            # Assign tags
            for tag_name in data.get('tags', []):
                tag, _ = BlogTag.objects.get_or_create(name=tag_name)
                post.tags.add(tag)
                
            # Assign products
            if products:
                post.related_products.set(products)

            # Assign FAQs
            BlogFAQ.objects.filter(post=post).delete()
            for i, faq_data in enumerate(data.get('faqs', [])):
                BlogFAQ.objects.create(post=post, question=faq_data['q'], answer=faq_data['a'], order=i)

        self.stdout.write(self.style.SUCCESS('Successfully populated blog data!'))
