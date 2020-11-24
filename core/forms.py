from django import forms
from django.contrib.auth import password_validation
from django.core.exceptions import ValidationError
from django.forms import PasswordInput
from .models import AdvUser, user_registered, Purchase, Customer


class ChangeUserInfoForm(forms.ModelForm):
    email = forms.EmailField(required=True, label='Адресс электронной почты')

    class Meta:
        model = AdvUser
        fields = ('first_name', 'last_name', 'username', 'email', 'company_name')


class RegisterUserForm(forms.ModelForm):
    email = forms.EmailField(required=True)
    password1 = forms.CharField(label='Пароль', widget=PasswordInput)
    password2 = forms.CharField(label='Пароль', widget=PasswordInput)

    def clean_password1(self):
        password1 = self.cleaned_data['password1']
        if password1:
            password_validation.validate_password(password1)
        return password1

    def clean(self):
        super().clean()
        password1 = self.cleaned_data['password1']
        password2 = self.cleaned_data['password2']
        if password1 and password2 and password1 != password2:
            errors = {'password2': ValidationError('Введенные пароли не совпадают', code='password_mismatch')}
            raise ValidationError(errors)

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data['password1'])
        user.is_active = False
        user.is_activated = False
        if commit:
            user.save()
        user_registered.send(RegisterUserForm, instance=user)
        return user

    class Meta:
        model = AdvUser
        fields = (
            'username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'company_name')
