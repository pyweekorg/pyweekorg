from django import forms
from django.contrib import auth


class ResetPasswordForm(forms.Form):
    email_address = forms.EmailField()


class LoginForm(forms.Form):
    """A username/password login form.

    The form validates the username and password provided; if the form
    validates then the validated User object can be accessed as
    ``form.cleaned_data['user']``.

    """
    username = forms.CharField()
    password = forms.CharField(widget=forms.PasswordInput())

    def clean(self):
        data = super().clean()
        username = data.get('username')
        password = data.get('password')

        if username and password:
            user = auth.authenticate(username=username, password=password)
            if user is None:
                raise forms.ValidationError(
                    "Invalid username or password. Please remember that "
                    "usernames and passwords are case sensitive."
                )

            data['user'] = user
        return data
