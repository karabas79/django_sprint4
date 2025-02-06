from django.core.paginator import Paginator
from django.db.models import Count
from django.utils import timezone

from blog.models import Post


def get_filter_posts(
        author=None,
        location=None,
        category=None,
        unpublished=False,
        not_user=False):
    """Фильтруем посты по дате, статусу публикации и категории."""
    filters = {}

    if not_user:
        filters['is_published'] = True
        filters['pub_date__lte'] = timezone.now()
        filters['category__is_published'] = True

    if author:
        filters['author'] = author
        if unpublished:
            filters.pop('is_published', None)

    if location:
        filters['location'] = location

    if category:
        filters['category'] = category

    posts = Post.objects.select_related(
        'author', 'location', 'category'
    ).annotate(
        comment_count=Count('comments')
    ).filter(**filters).order_by('-pub_date')

    return posts


def paginate_func(request, queryset, items_per_page):
    return Paginator(queryset, items_per_page).get_page(
        request.GET.get('page'))
