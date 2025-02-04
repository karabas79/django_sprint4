from django.core.paginator import Paginator
from django.utils import timezone

from django.db.models import Count

from blog.models import Post


def get_filter_posts(
        author=None,
        location=None,
        category=None,
        unpublished=False):
    """Фильтруем посты по дате, статусу публикации и категории."""
    filters = {
        'pub_date__lte': timezone.now(),
        'is_published': True,
        'category__is_published': True
    }

    if unpublished:
        filters.pop('is_published')

    if author:
        filters['author'] = author

    if location:
        filters['location'] = location

    if category:
        filters['category'] = category

    return Post.objects.select_related('category').annotate(
        comment_count=Count('comments')
    ).filter(**filters).order_by('-pub_date')


def paginate_func(request, queryset, items_per_page):
    return Paginator(queryset, items_per_page).get_page(request.GET.get('page'))
