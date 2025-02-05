
from blog.constants import NUMBER_POSTS
from blog.form import CommentForm, PostForm, RegistrationForm
from blog.models import Category, Comment, Post
from blog.service import get_filter_posts, get_sorted_queryset, paginate_func
from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.exceptions import PermissionDenied
from django.core.mail import send_mail
from django.db.models import Count
from django.http import Http404
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone


def index(request):
    posts = get_filter_posts()

    page_obj = paginate_func(request, posts, NUMBER_POSTS)
    context = {'page_obj': page_obj}
    return render(request, 'blog/index.html', context)


def post_detail(request, post_id):

    post = get_object_or_404(Post, id=post_id)

    if (
        not (post.is_published
             and post.category.is_published
             and post.pub_date <= timezone.now())
        and post.author != request.user
    ):
        raise Http404("Пост не найден.")

    comments = post.comments.all().order_by('created_at')
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

    posts = get_filter_posts(category=category)

    page_obj = paginate_func(request, posts, NUMBER_POSTS)

    context = {
        'category': category_slug,
        'page_obj': page_obj
    }
    return render(request, 'blog/category.html', context)


@login_required(login_url='login')
def create_post(request):
    form = PostForm(request.POST or None, request.FILES or None)

    if form.is_valid():
        post = form.save(commit=False)
        post.author = request.user
        post.save()
        confirm_create_post(request.user.email)
        return redirect('blog:profile', username=request.user.username)

    return render(request, 'blog/create.html', {'form': form})


@login_required(login_url='login')
def edit_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(request.POST or None, request.FILES or None, instance=post)

    if post.author != request.user:
        return redirect('blog:post_detail', post_id=post.id)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post.id)

    return render(request, 'blog/create.html', {'form': form, 'post': post})


@login_required(login_url='login')
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = PostForm(instance=post)

    if post.author != request.user:
        raise Http404("У вас нет прав для удаления этого поста.")

    if request.method == 'POST':
        post.delete()
        return redirect('blog:index')

    return render(
        request,
        'blog/create.html',
        {'post': post, 'form': form}
    )


def profile(request, username):
    user_profile = get_object_or_404(User, username=username)
    not_user = request.user != user_profile

    posts = get_sorted_queryset(user_profile, not_user)

    page_obj = paginate_func(request, posts, NUMBER_POSTS)

    context = {
        'profile': user_profile,
        'page_obj': page_obj,
    }

    return render(request, 'blog/profile.html', context)


@login_required(login_url='login')
def edit_profile(request):
    user = request.user
    form = RegistrationForm(request.POST or None, instance=user)

    if form.is_valid():
        form.save()
        return redirect('blog:profile', username=user.username)

    return render(
        request,
        'registration/registration_form.html',
        {'form': form}
    )


@login_required(login_url='login')
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    form = CommentForm(request.POST or None)

    if form.is_valid():
        comment = form.save(commit=False)
        comment.post = post
        comment.author = request.user
        comment.save()
        return redirect('blog:post_detail', post_id=post.id)

    return render(request, 'blog/comment.html', {'post': post, 'form': form})


@login_required(login_url='login')
def edit_comment(request, post_id, comment_id):
    comment = get_object_or_404(Comment, id=comment_id)

    if comment.author != request.user:
        raise PermissionDenied(
            "У вас нет прав для редактирования данного комментария."
        )
    form = CommentForm(request.POST or None, instance=comment)

    if form.is_valid():
        form.save()
        return redirect('blog:post_detail', post_id=post_id)

    return render(
        request, 'blog/comment.html',
        {'form': form, 'comment': comment}
    )


@login_required(login_url='login')
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
        from_email=settings.EMAIL_BLOGICUM,
        recipient_list=[email],
        fail_silently=True,
    )
