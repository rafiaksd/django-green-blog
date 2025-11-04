from django import forms
from .models import Comment

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
