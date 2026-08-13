from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import BlogCategory, BlogPost


def post_list(request):
    posts = BlogPost.objects.filter(is_published=True).select_related('category')
    categories = BlogCategory.objects.filter(is_active=True)
    category_slug = request.GET.get('category')
    if category_slug:
        posts = posts.filter(category__slug=category_slug)
    return render(request, 'blog/post_list.html', {
        'posts': posts,
        'categories': categories,
        'active_category': category_slug,
    })


def post_detail(request, slug):
    post = get_object_or_404(
        BlogPost.objects.select_related('category', 'author'),
        slug=slug,
        is_published=True,
    )
    related = BlogPost.objects.filter(
        is_published=True, category=post.category
    ).exclude(pk=post.pk)[:3]
    return render(request, 'blog/post_detail.html', {
        'post': post,
        'related_posts': related,
    })
