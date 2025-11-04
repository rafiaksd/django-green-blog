from django import forms
from .models import Comment

from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(max_length=254, required=True, widget=forms.EmailInput(attrs={'class': 'w-full px-4 py-2 border-2 border-gray-300 rounded-md focus:outline-none focus:ring-2 focus:ring-treegreen', 'placeholder': 'Enter your email'}))

    class Meta:
        model = User
        fields = ['username', 'email', 'password1', 'password2']
        
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['content']
        widgets = {
            'content': forms.Textarea(attrs={
                'class': 'w-full border-2 border-black p-3 rounded-md',
                'rows': 3,
                'placeholder': 'Write your comment here...'
            })
        }
