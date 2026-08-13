from django.shortcuts import render, get_object_or_404
from django.db.models import Q
from core.homepage_context import build_luxury_page_context
from .models import (
    Product, Collection, FragranceFamily, Occasion, GiftSet, RecentlyViewed,
)
from .filters import ProductFilter
from .fragrance_utils import SIGNATURE_SKUS


def collection_landing(request):
    """Dedicated collection page — detailed fragrance catalog, not a duplicate of home."""
    context = build_luxury_page_context()
    return render(request, 'products/collection_landing.html', context)


def shop(request):
    products = Product.objects.filter(is_active=True, sku__in=SIGNATURE_SKUS).distinct()
    product_filter = ProductFilter(request.GET, queryset=products)
    products = product_filter.qs

    sort = request.GET.get('sort', '-created_at')
    sort_map = {
        'price_low': 'regular_price',
        'price_high': '-regular_price',
        'name': 'name',
        'newest': '-created_at',
        'popular': '-is_best_seller',
    }
    products = products.order_by(sort_map.get(sort, '-created_at'))

    return render(request, 'products/shop.html', {
        'products': products,
        'filter': product_filter,
        'sort': sort,
        'fragrance_families': FragranceFamily.objects.all(),
        'occasions': Occasion.objects.all(),
        'collections': Collection.objects.filter(is_active=True),
    })


def product_detail(request, slug):
    product = get_object_or_404(Product, slug=slug, is_active=True)
    related = Product.objects.filter(
        is_active=True,
        fragrance_families__in=product.fragrance_families.all(),
    ).exclude(id=product.id).distinct()[:4]

    if request.user.is_authenticated:
        RecentlyViewed.objects.update_or_create(
            user=request.user, product=product,
            defaults={'session_key': ''},
        )
    elif request.session.session_key:
        RecentlyViewed.objects.update_or_create(
            session_key=request.session.session_key, product=product, user=None,
        )

    recently_viewed = RecentlyViewed.objects.filter(
        Q(user=request.user) if request.user.is_authenticated else Q(session_key=request.session.session_key)
    ).exclude(product=product)[:4]

    return render(request, 'products/product_detail.html', {
        'product': product,
        'related_products': related,
        'recently_viewed': recently_viewed,
    })


def collection_list(request):
    collections = Collection.objects.filter(is_active=True)
    return render(request, 'products/collections.html', {'collections': collections})


def collection_detail(request, slug):
    collection = get_object_or_404(Collection, slug=slug, is_active=True)
    products = collection.products.filter(is_active=True)
    return render(request, 'products/product_list.html', {
        'products': products,
        'title': collection.name,
        'subtitle': collection.description,
    })


def fragrance_family(request, slug):
    family = get_object_or_404(FragranceFamily, slug=slug)
    products = family.products.filter(is_active=True)
    return render(request, 'products/product_list.html', {
        'products': products,
        'title': family.get_name_display(),
        'subtitle': family.description or f'Shop {family.get_name_display()} fragrances',
    })


def occasion(request, slug):
    occasion_obj = get_object_or_404(Occasion, slug=slug)
    products = occasion_obj.products.filter(is_active=True)
    return render(request, 'products/product_list.html', {
        'products': products,
        'title': occasion_obj.get_name_display(),
        'subtitle': occasion_obj.description or f'Perfumes for {occasion_obj.get_name_display()}',
    })


def best_sellers(request):
    products = Product.objects.filter(is_active=True, is_best_seller=True)
    return render(request, 'products/best_sellers.html', {
        'products': products, 'title': 'Best Sellers', 'subtitle': 'Our most popular fragrances',
    })


def new_arrivals(request):
    products = Product.objects.filter(is_active=True, is_new_arrival=True)
    return render(request, 'products/new_arrivals.html', {
        'products': products, 'title': 'New Arrivals', 'subtitle': 'Freshly launched perfumes',
    })


def gift_sets(request):
    sets = GiftSet.objects.filter(is_active=True)
    return render(request, 'products/gift_sets.html', {'gift_sets': sets})


def gift_set_detail(request, slug):
    gift_set = get_object_or_404(GiftSet, slug=slug, is_active=True)
    return render(request, 'products/gift_set_detail.html', {'gift_set': gift_set})
