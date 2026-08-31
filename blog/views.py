from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .models import BlogCategory, BlogPost


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

    return render(request, 'blog/post_list.html', {
        'featured_post': featured_post,
        'page_obj': page_obj,
        'categories': categories,
        'active_category': category_slug or 'all',
        'search_query': search_query,
        'popular_posts': popular_posts,
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
