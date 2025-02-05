from blog.models import Category, Comment, Location, Post
from django.contrib import admin

admin.site.empty_value_display = 'Не задано'


class PostInline(admin.StackedInline):
    model = Post
    extra = 0


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    inlines = (
        PostInline,
    )
    list_display = (
        'title',
    )


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title',
        'pub_date',
        'author',
        'category',
        'location',
        'is_published'
    )
    list_editable = (
        'is_published',
        'pub_date',
        'category'
    )
    search_fields = ('title',)
    list_filter = ('category',)
    list_display_links = ('title',)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = (
        'post',
        'author',
        'created_at',
        'is_published'
    )
    list_editable = ('is_published',)
    search_fields = ('author__username', 'post__title')
    list_filter = ('is_published', 'post')


admin.site.register(Location)
