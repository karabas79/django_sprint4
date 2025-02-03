from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.core.paginator import Paginator
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse
from django.utils import timezone

from .constants import NUMBER_POSTS
from .form import PostForm, RegistrationForm, CommentForm
from .models import Category, Post, Comment


def get_filter_posts(author=None, location=None, unpublished=False):
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

    post = get_object_or_404(Post, id=post_id)

    is_author = post.author == request.user

    if not post.is_published:
        if not is_author:
            raise Http404("Пост не найден или еще не опубликован.")

    if not post.category.is_published and not is_author:
        raise Http404("Пост не найден или снят с публикации.")

    if post.pub_date > timezone.now() and not is_author:
        raise Http404("Пост не найден или еще не опубликован.")

    comments = post.comment.all().order_by('created_at')
    form = CommentForm()
    return render(request, 'blog/detail.html', {
        'post': post,
        'comments': comments,
        'form': form,
        'pub_date': post.pub_date,
    })


def category_posts(request, category_slug):
    category = get_object_or_404(
        Category,
        slug=category_slug,
        is_published=True
    )

    posts = get_filter_posts().filter(category=category).order_by('-pub_date')

    paginator = Paginator(posts, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    context = {
        'category': category_slug,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


@login_required(login_url='/auth/login/')
def create_post(request):

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.is_published = post.pub_date <= timezone.now()
            post.save()
            confirm_create_post(request.user.email)
            return redirect('blog:profile', username=request.user.username)
    else:
        form = PostForm()

    return render(request, 'blog/create.html', {'form': form})


@login_required(login_url='/auth/login/')
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author != request.user:
        return redirect(reverse(
            'blog:post_detail',
            kwargs={'post_id': post.id})
        )

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES, instance=post)
        if form.is_valid():
            post.is_published = post.pub_date <= timezone.now()
            form.save()
            return redirect(reverse(
                'blog:post_detail',
                kwargs={'post_id': post.id})
            )
    else:
        form = PostForm(instance=post)

    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required(login_url='/auth/login/')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if post.author == request.user:
        post.delete()
        return redirect('blog:index')
    else:
        return redirect('blog:post_detail', post_id=post.id)


def profile(request, username):
    print(f"Requested username: {username}")
    user_profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=user_profile).annotate(
        comment_count=Count('comment')
    ).order_by('-pub_date')
    paginator = Paginator(posts, NUMBER_POSTS)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {
        'profile': user_profile,
        'page_obj': page_obj,
        'post_count': posts.count()
    }

    return render(request, 'blog/profile.html', context)


@login_required(login_url='/auth/login/')
def edit_profile(request):
    user = request.user
    print(f"Requested user: {user}")

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


@login_required(login_url='/auth/login/')
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


@login_required(login_url='/auth/login/')
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        raise PermissionDenied(
            "У вас нет прав для редактирования данного комментария."
        )
    form = CommentForm(instance=comment)

    if request.method == 'POST':
        form = CommentForm(request.POST, instance=comment)
        if form.is_valid():
            form.save()
            return redirect('blog:post_detail', post_id=post_id)

    return render(
        request, 'blog/comment.html',
        {'form': form, 'comment': comment}
    )


@login_required(login_url='/auth/login/')
def delete_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        raise PermissionDenied(
            "У вас нет прав для удаления данного комментария."
        )

    if request.method == 'POST':
        comment.delete()
        return redirect('blog:post_detail', post_id=post_id)

    return render(request, 'blog/comment.html', {'comment': comment})


def confirm_create_post(email):
    send_mail(
        subject='Привет!',
        message='Спасибо, что разместил у нас свой пост!',
        from_email='confirm_form@blogicum.ru',
        recipient_list=[email],
        fail_silently=True,
    )
