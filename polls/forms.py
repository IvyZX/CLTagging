from polls.models import UserProfile, Tag
from django.contrib.auth.models import User
from django import forms


class UserForm(forms.ModelForm):
    username = forms.CharField()
    expert = forms.ChoiceField(required=True, choices=((True, 'Expert'), (False, 'Novice')))
    nominal = forms.ChoiceField(required=True, choices=((True, 'Nominal'), (False, 'Social')))

    class Meta:
        model = User
        fields = ('username', 'expert', 'nominal')


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile

class AddTagForm(forms.ModelForm):
    tag = forms.CharField(max_length=100)

    class Meta:
        model = Tag
        fields = ('tag',)

# class voteTagForm(forms.ModelForm):
