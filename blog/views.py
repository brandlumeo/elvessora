from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import BlogCategory, BlogPost
from products.models import Product


def _category_link(name):
    """Best-effort lookup of a real category by name for the knowledge
    section's links — returns its slug, or None if it doesn't exist
    (the template falls back to the plain blog list in that case)."""
    return BlogCategory.objects.filter(name__iexact=name, is_active=True).values_list('slug', flat=True).first()


def post_list(request):
    posts_qs = BlogPost.objects.filter(is_published=True).select_related('category')
    categories = BlogCategory.objects.filter(is_active=True)

    # Handle search
    search_query = request.GET.get('q', '').strip()
    if search_query:
        posts_qs = posts_qs.filter(
            Q(title__icontains=search_query) |
            Q(excerpt__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(tags__name__icontains=search_query)
        ).distinct()

    # Handle category filtering
    category_slug = request.GET.get('category')
    if category_slug and category_slug != 'all':
        posts_qs = posts_qs.filter(category__slug=category_slug)

    # Get featured post (only on first page and if no search query)
    featured_post = None
    if not search_query and not category_slug:
        featured_post = posts_qs.filter(is_featured=True).first()
        if featured_post:
            posts_qs = posts_qs.exclude(id=featured_post.id)

    # Pagination
    paginator = Paginator(posts_qs, 9)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Popular posts
    popular_posts = BlogPost.objects.filter(is_published=True).order_by('-views')[:3]

    # "Shop the Stories" — real products actually referenced by a published
    # article; falls back to a handful of active catalog products if no
    # article has been linked to one yet. Never fabricated.
    shop_products = list(
        Product.objects.filter(is_active=True, blog_posts__is_published=True)
        .distinct()
        .select_related('brand')[:4]
    )
    if not shop_products:
        shop_products = list(Product.objects.filter(is_active=True).select_related('brand')[:4])

    # "Discover the World of Fragrance" — links to real categories/pages
    # where they exist; the template falls back to the plain blog list
    # for any that don't resolve, so nothing here is ever a dead link.
    knowledge_blocks = [
        {
            'title': 'Fragrance Families',
            'description': 'Floral, woody, oriental, fresh — find the family that matches your taste.',
            'image': '/media/products/ChatGPT_Image_Aug_4_2026_06_56_44_PM.png',
            'url': None,
            'url_name': 'quiz:finder',
        },
        {
            'title': 'Understanding Fragrance Notes',
            'description': 'How top, heart, and base notes unfold on your skin over time.',
            'image': '/media/products/ChatGPT_Image_Aug_4_2026_06_56_56_PM.png',
            'category_slug': _category_link('Fragrance Notes'),
        },
        {
            'title': 'The Art of Perfume',
            'description': 'Behind the craftsmanship, ingredients, and stories of fine perfumery.',
            'image': '/media/products/ChatGPT_Image_Aug_4_2026_06_57_01_PM.png',
            'category_slug': _category_link('Perfume Guides'),
        },
        {
            'title': 'Choosing Your Signature Scent',
            'description': 'A personal journey — how fragrance, personality, and occasion come together.',
            'image': '/media/products/ChatGPT_Image_Aug_4_2026_06_57_06_PM.png',
            'post_slug': BlogPost.objects.filter(
                is_published=True, title__icontains='Signature Scent'
            ).values_list('slug', flat=True).first(),
        },
    ]

    return render(request, 'blog/post_list.html', {
        'featured_post': featured_post,
        'page_obj': page_obj,
        'categories': categories,
        'active_category': category_slug or 'all',
        'search_query': search_query,
        'popular_posts': popular_posts,
        'shop_products': shop_products,
        'knowledge_blocks': knowledge_blocks,
    })


def post_detail(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related('category', 'author'),
        slug=slug,
        is_published=True,
    )

    # Increment views
    post.views += 1
    post.save(update_fields=['views'])

    related = BlogPost.objects.filter(
        is_published=True, category=post.category
    ).exclude(pk=post.pk)[:3]

    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related_posts': related,
    })
