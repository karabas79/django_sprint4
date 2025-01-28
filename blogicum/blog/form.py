from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Post, Comment


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        fields = ['title', 'text', 'image', 'pub_date', 'category', 'location']
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'}
            )
        }


class RegistrationForm(UserCreationForm):
    email = forms.EmailField(required=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']


class CommentForm(forms.ModelForm):

    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={
                'class':
                'form-control',
                'placeholder':
                'Введите ваш комментарий'}),
        }

    def clean_text(self):
        text = self.cleaned_data.get('text')
        if not text:
            raise ValidationError('Комментарий не может быть пустым.')
        if len(text) > 500:  # Пример ограничения длины
            raise ValidationError(
                'Комментарий не может превышать 500 символов.'
            )
        return text
