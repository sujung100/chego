from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.contrib.auth.models import User
from calendar_app.models import Store, Manager, Reservation_user
from django.core.validators import RegexValidator
from manager.validators import username_validator, phone_validator

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

class ManagerUpdateForm(forms.ModelForm):
    class Meta:
        model = Manager
        fields = ['user', 'manager_name', 'manager_phone']
        

class StoreUpdateForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['id', 'owner']

class UpdateForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['id', 'store_name', 'address', 'owner']

class TotalReservationForm(forms.ModelForm):
    class Meta:
        model = Store
        fields = ['id', 'owner']

# 회원가입 - 전화번호
class ManagerSignUpForm(UserCreationForm):
    phone_number = forms.CharField(
        max_length=13,
        label="핸드폰 번호",
        validators=[phone_validator],
    )

    class Meta(UserCreationForm.Meta):
        model = User
        fields = ("username",)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        field = self.fields["username"]
        field.max_length = 16
        field.widget.attrs["maxlength"] = 16
        field.validators = [username_validator]
        field.help_text = ""


# class ManagerUpdateForm(forms.ModelForm):
#     class Meta:
#         model = Store
#         fields = ['id', 'store_name', 'address', 'owner']

