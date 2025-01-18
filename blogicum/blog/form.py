from django import forms
# from django.contrib.auth import get_user_model

from .models import Post  # , Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['title', 'text', 'pub_date', 'category', 'location']
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'}
            )
        }


# class CommentForm(forms.ModelForm):

#     class Meta:
#         model = Comment
#         fields = ['text']
