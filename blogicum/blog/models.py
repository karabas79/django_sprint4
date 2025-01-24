from django.contrib.auth import get_user_model
from django.db import models

from .constants import NUMBER_CHARACTERS
from core.models import CreatedModel, PublishedModel

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
        help_text=(
            'Если установить дату и время в будущем — можно делать '
            'отложенные публикации.'
        )
    )
    description = models.TextField('Описание')
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


class Comment(models.Model):
    text = models.TextField('Комментарии')
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comment',
    )
    created_at = models.DateTimeField(auto_now_add=True)
    author = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        ordering = ('created_at',)


class StaticPage(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    content = models.TextField()

    def __str__(self):
        return self.title
