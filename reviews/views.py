from django.shortcuts import redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from products.models import Product
from .forms import ReviewForm
from .models import Review


@login_required
def add_review(request, product_slug):
    product = get_object_or_404(Product, slug=product_slug, is_active=True)
    if Review.objects.filter(user=request.user, product=product).exists():
        messages.warning(request, 'You have already reviewed this product.')
        return redirect('products:product_detail', slug=product_slug)

    form = ReviewForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        review = form.save(commit=False)
        review.user = request.user
        review.product = product
        review.save()
        messages.success(request, 'Thank you! Your review has been submitted for approval.')
        return redirect('products:product_detail', slug=product_slug)

    return redirect('products:product_detail', slug=product_slug)
