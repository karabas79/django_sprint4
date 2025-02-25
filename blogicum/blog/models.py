from core.models import CreatedModel, PublishedModel
from django.contrib.auth import get_user_model
from django.db import models
from django.urls import reverse
from django.utils import timezone

from blog.constants import NUMBER_CHARACTERS

User = get_user_model()


class Category(PublishedModel, CreatedModel):
    title = models.CharField('Заголовок', max_length=256)
    slug = models.SlugField(
        'Идентификатор',
        max_length=64,
        unique=True,
        help_text=(
            'Идентификатор страницы для URL; '
            'разрешены символы латиницы, цифры, дефис и подчёркивание.'
        )
    )
    description = models.TextField('Описание')

    class Meta:
        verbose_name = 'категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.title[:NUMBER_CHARACTERS]


class Location(PublishedModel, CreatedModel):
    name = models.CharField(
        'Название места',
        max_length=256
    )

    class Meta:
        verbose_name = 'местоположение'
        verbose_name_plural = 'Местоположения'

    def __str__(self):
        return self.name


class Post(PublishedModel, CreatedModel):
    title = models.CharField('Название', max_length=256)
    text = models.TextField('Текст')
    image = models.ImageField('Фото', upload_to='blog_images', blank=True)
    pub_date = models.DateTimeField(
        'Дата и время публикации',
        default=timezone.now,
        help_text=(
            'Если установить дату и время в будущем — можно делать '
            'отложенные публикации.'
        )
    )
    description = models.TextField('Описание', blank=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Автор публикации'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        verbose_name='Категория',
        null=True,
    )
    location = models.ForeignKey(
        Location,
        on_delete=models.SET_NULL,
        verbose_name='Местоположение',
        null=True,
        blank=True,
    )

    def comment_count(self):
        return self.comment.count()

    class Meta:
        verbose_name = 'публикация'
        verbose_name_plural = 'Публикации'
        ordering = ['-pub_date']
        default_related_name = 'posts'

    def __str__(self):
        return self.title[:NUMBER_CHARACTERS]

    def is_visible(self):
        """Проверяет, доступен ли пост для просмотра."""
        return self.is_published or (
            self.publish_date and self.publish_date <= timezone.now()
        )

    def get_absolute_url(self):
        """Возвращает канонический URL для просмотра поста."""
        return reverse('blog:post_detail', kwargs={'post_id': self.id})


class Comment(PublishedModel, CreatedModel):
    text = models.TextField('Комментарии')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='comments'
    )

    class Meta:
        verbose_name = 'комментарий'
        verbose_name_plural = 'Комментарии'
        ordering = ('created_at',)

    def __str__(self):
        return (
            f'Комментарий автора {self.author.username} '
            f'к посту "{self.post}, '
            f'текст: "{self.text[:NUMBER_CHARACTERS]}..."'
        )


class StaticPage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()

    def __str__(self):
        return self.title
