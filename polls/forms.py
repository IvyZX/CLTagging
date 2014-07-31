from polls.models import UserProfile, Tag
from django.contrib.auth.models import User
from django import forms


class UserForm(forms.ModelForm):
    username = forms.CharField()
    email = forms.EmailField()
    password = forms.CharField(widget=forms.PasswordInput())
    expert = forms.NullBooleanField()
    nominal = forms.NullBooleanField()

    class Meta:
        model = User
        fields = ('username', 'email', 'password', 'expert', 'nominal')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile

class AddTagForm(forms.ModelForm):
    tag = forms.CharField(max_length=100)

    class Meta:
        model = Tag
        fields = ('tag',)

# class voteTagForm(forms.ModelForm):
