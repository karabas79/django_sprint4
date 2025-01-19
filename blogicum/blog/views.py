from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.paginator import Paginator
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone

# from .constants import NUMBER_POSTS_ON_MAIN
from .form import PostForm, RegistrationForm
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
    posts = get_filter_posts().order_by('-pub_date')

    # Пагинация
    paginator = Paginator(posts, 10)  # 10 публикаций на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    # posts = get_filter_posts()  # [:NUMBER_POSTS_ON_MAIN]
    context = {'page_obj': page_obj}
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

    page_obj = get_filter_posts(
        author=author,
        location=location
    ).filter(category=category)

    context = {
        'category': category_slug,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


@login_required
def create_post(request):
    form = PostForm()
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def post_edit(request, post_id):
    pass


def profile(request, username):
    profile = get_object_or_404(User, username=username)

    # Получаем публикации пользователя
    posts = Post.objects.filter(author=profile).order_by('-pub_date')

    # Пагинация
    paginator = Paginator(posts, 10)  # 10 публикаций на странице
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'profile': profile,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    if request.method == 'POST':
        # Логика для обработки формы редактирования профиля
        pass
    return render(request, 'blog/profile.html')


@login_required
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Вход пользователя после регистрации
            return redirect('blog:profile', username=user.username)
    else:
        form = RegistrationForm()
    return render(request, 'registration/register.html', {'form': form})


@login_required
def profile_redirect(request):
    return HttpResponseRedirect(
        reverse('blog:profile', args=[request.user.username])
    )
