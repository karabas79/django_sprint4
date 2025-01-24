from django.contrib.auth import login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.utils import timezone

from .constants import NUMBER_POSTS
from .form import PostForm, RegistrationForm, CommentForm, StaticPageForm
from .models import Category, Post, Comment, StaticPage


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
    return Post.objects.select_related('category').annotate(
        comment_count=Count('comment')
    ).filter(**filters)


def index(request):
    posts = get_filter_posts().order_by('-pub_date')

    paginator = Paginator(posts, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
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
    comments = post.comment.all()
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
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
        form = PostForm(request.POST, request.FILES)
    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        confirm_create_post(request.user.email)
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html', {'form': form})


@login_required
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/create.html', {'form': form})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author == request.user:
        post.delete()
        return redirect('blog:profile', username=request.user.username)
    else:
        return redirect('blog:post_detail', post_id=post.id)


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user_profile).annotate(
        comment_count=Count('comment')
    ).order_by('-pub_date')
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': user_profile,
        'page_obj': page_obj,
    }
    return render(request, 'blog/profile.html', context)


@login_required
def edit_profile(request):
    user = request.user

    if request.method == 'POST':
        form = RegistrationForm(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)
    else:
        form = RegistrationForm(instance=user)

    return render(
        request,
        'registration/registration_form.html',
        {'form': form}
    )


@login_required
def register_view(request):
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            return redirect('blog:profile', username=user.username)
    else:
        form = RegistrationForm()
    return render(
        request,
        'registration/registration_form.html',
        {'form': form}
    )


def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
            return redirect('blog:post_detail', post_id=post.id)
    else:
        form = CommentForm()

    return render(request, 'blog/comment.html', {'post': post, 'form': form})


def edit_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        return redirect('blog:post_detail', post_id=comment.post.id)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=comment.post.id)
    else:
        form = CommentForm(instance=comment)

    return render(
        request, 'blog/edit_comment.html',
        {'form': form, 'comment': comment}
    )


def delete_comment(request, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author == request.user:
        post_id = comment.post.id
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)
    else:
        return redirect('blog:post_detail', post_id=comment.post.id)


def confirm_create_post(email):
    send_mail(
        subject='Hello!',
        message='Thanks for posting!',
        from_email='confirm_form@blogicum.ru',
        recipient_list=[email],
        fail_silently=True,
    )


class StaticPageListView(ListView):
    """Шаблон для списка страниц"""

    model = StaticPage
    template_name = 'static_pages/static_page_list.html'


class StaticPageDetailView(DetailView):
    """Шаблон для отображения страницы"""

    model = StaticPage
    template_name = 'static_pages/static_page_detail.html'


class StaticPageCreateView(CreateView):
    """Перенаправление после успешного создания"""

    model = StaticPage
    form_class = StaticPageForm
    template_name = 'static_pages/static_page_form.html'
    success_url = reverse_lazy('static_page_list')


class StaticPageUpdateView(UpdateView):
    """Перенаправление после успешного обновления"""

    model = StaticPage
    form_class = StaticPageForm
    template_name = 'static_pages/static_page_form.html'
    success_url = reverse_lazy('static_page_list')
