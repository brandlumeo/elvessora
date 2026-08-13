import django_filters
from django.db.models import Q
from .models import Product


class ProductFilter(django_filters.FilterSet):
    q = django_filters.CharFilter(method='search_filter', label='Search')
    min_price = django_filters.NumberFilter(field_name='regular_price', lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name='regular_price', lookup_expr='lte')
    gender = django_filters.ChoiceFilter(choices=Product.GENDER_CHOICES)
    concentration = django_filters.ChoiceFilter(choices=Product.CONCENTRATION_CHOICES)
    fragrance_family = django_filters.CharFilter(field_name='fragrance_families__slug')
    occasion = django_filters.CharFilter(field_name='occasions__slug')
    collection = django_filters.CharFilter(field_name='collection__slug')
    category = django_filters.CharFilter(field_name='category__slug')

    class Meta:
        model = Product
        fields = ['gender', 'concentration']

    def search_filter(self, queryset, name, value):
        return queryset.filter(
            Q(name__icontains=value)
            | Q(description__icontains=value)
            | Q(top_notes__icontains=value)
            | Q(heart_notes__icontains=value)
            | Q(base_notes__icontains=value)
            | Q(sku__icontains=value)
        )
