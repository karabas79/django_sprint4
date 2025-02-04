from django import forms
from django.contrib.auth.models import User
from django.core.exceptions import ValidationError

from .models import Comment, Post


class PostForm(forms.ModelForm):

    class Meta:
        model = Post
        exclude = ['is_published', 'description', 'author']
        widgets = {
            'pub_date': forms.DateTimeInput(
                format='%Y-%m-%dT%H:%M',
                attrs={'type': 'datetime-local'}
            )
        }


class RegistrationForm(forms.ModelForm):

    class Meta:
        model = User
        fields = ('first_name', 'last_name', 'username', 'email')

    def clean_username(self):
        username = self.cleaned_data.get('username')
        if User.objects.exclude(pk=self.instance.pk).filter(
            username=username
        ).exists():
            raise forms.ValidationError("Это имя пользователя уже занято.")
        return username

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.exclude(pk=self.instance.pk).filter(
            email=email
        ).exists():
            raise forms.ValidationError(
                "Этот адрес электронной почты уже занят."
            )
        return email


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
        return text
