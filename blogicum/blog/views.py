from django.shortcuts import get_object_or_404, render
from django.utils import timezone

from .constants import NUMBER_POSTS_ON_MAIN
from .form import PostForm
from .models import Category, Post


def get_filter_posts(author=None, location=None):
    """Фильтруем посты по дате, статусу публикации и категории."""
    filters = {
        'pub_date__lte': timezone.now(),
        'is_published': True,
        'category__is_published': True
    }

    if author:
        filters['author'] = author
    if location:
        filters['location'] = location
    return Post.objects.select_related('category').filter(**filters)


def index(request):
    post_list = get_filter_posts()[:NUMBER_POSTS_ON_MAIN]
    context = {'post_list': post_list}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):
    """Фильтруем посты по дате ИЛИ статусу публикации ИЛИ категории, к которой
    принадлежит публикация.
    """
    post = get_object_or_404(
        get_filter_posts(),
        id=post_id,
    )
    context = {'post': post}
    return render(request, 'blog/detail.html', context)


def category_posts(request, category_slug):
    category = get_object_or_404(  # Получаем категорию по slug
        Category,
        slug=category_slug,
        is_published=True
    )

    author = request.GET.get('author')
    location = request.GET.get('location')

    post_list = get_filter_posts(
        author=author,
        location=location
    ).filter(category=category)

    context = {
        'category': category_slug,
        'post_list': post_list
    }
    return render(request, 'blog/category.html', context)


# def login_view(request):
#     return render(request, 'registration/login.html')


def create_post(request):
    form = PostForm(request.POST or None)
    context = {'form': form}
    if form.is_valid():
        form.save()
    return render(request, 'blog/create.html', context)


def post_edit(request, post_id):
    pass


def profile(request, username):
    pass


# def logout_view(request):
#     return render(request, 'registration/logged_out.html')
