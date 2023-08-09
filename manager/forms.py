from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User

class UserCreationForm(UserCreationForm):
    email = forms.EmailField(label='Email', max_length=255, required=False)
    phone_number = forms.CharField(label='Phone number', max_length=15, required=True)

    class Meta:
        model = User
        fields = ("username", "password1", "password2", "phone_number", "email")

    # def save(self, commit=True):
    #     user = super().save(commit=False)
    #     user.email = self.cleaned_data["email"]

    #     if commit:
    #         user.save()
    #     return user