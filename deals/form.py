from django import forms
from .models import Comment


class PasswordResetRequestForm(forms.Form):
    email = forms.EmailField(label="Email", max_length=254)


class CommentForm(forms.ModelForm):
    class Meta:
        model = Comment
        fields = ['comment']  # Adjust according to your comment fields
