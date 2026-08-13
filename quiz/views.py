from django.shortcuts import render

from .finder_catalog import build_finder_catalog


def perfume_finder(request):
    catalog = build_finder_catalog()
    return render(request, 'quiz/finder.html', {
        'finder_catalog': catalog,
    })
