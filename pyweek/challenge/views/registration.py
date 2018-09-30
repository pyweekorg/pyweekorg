from inspect import cleandoc

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django import forms
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.contrib import auth, messages

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

from ..forms import LoginForm
from ..models import Challenge


def is_registration_open():
    """Return True if registration is currently open."""
    c = Challenge.objects.latest()
    return c and c.isRegoOpen()


class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=15, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    again = forms.CharField(widget=forms.PasswordInput)
    captcha = ReCaptchaField(widget=ReCaptchaWidget())


def register(request):
    if not is_registration_open():
        return HttpResponseForbidden(
            "Registration is not available at the current time. "
            "Please check back when a challenge is scheduled."
        )

    redirect_to = request.GET.get('next', '')
    if request.POST:
        f = RegistrationForm(request.POST)
        if f.is_valid():
            if not f.cleaned_data['password']:
                f.errors['password'] = ['This field is required.']
            if f.cleaned_data['password'] != f.cleaned_data['again']:
                f.errors['again'] = ['Does not match password.']
            if User.objects.filter(username__exact=f.cleaned_data['name']):
                f.errors['name'] = ['Username already registered']
            if User.objects.filter(email__exact=f.cleaned_data['email']):
                f.errors['email'] = ['Email address already registered']
            if not f.errors:
                User.objects.create_user(f.cleaned_data['name'],
                    f.cleaned_data['email'], f.cleaned_data['password'])
                user = auth.authenticate(username=f.cleaned_data['name'],
                    password=f.cleaned_data['password'])
                auth.login(request, user)
                messages.info(request, 'Welcome to the Challenge!')
                return HttpResponseRedirect(redirect_to or '/')
    else:
        f = RegistrationForm()
    return render(request, 'registration/register.html', {'form': f})


def profile(request):
    redirect_to = request.GET.get('next', '')
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    elif request.POST:
        f = RegistrationForm(request.POST)
        if f.is_valid():
            if f.cleaned_data['password'] != f.cleaned_data['again']:
                f.errors['again'] = ['Does not match password.']
            if not f.errors:
                request.user.username = f.cleaned_data['name']
                request.user.email = f.cleaned_data['email']
                if f.cleaned_data['password']:
                    request.user.set_password(f.cleaned_data['password'])
                request.user.save()
                messages.success(request, 'Changes saved!')
                return HttpResponseRedirect(redirect_to or '/')
    else:
        f = RegistrationForm(initial={
            'name': request.user.username,
            'email': request.user.email,
        })
    return render(request, 'registration/profile.html', {'form': f})


def login_page(request, message=None, error=None):
    "Displays the login form and handles the login action."
    redirect_to = request.GET.get('next', '')

    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            auth.login(request, form.cleaned_data['user'])
            return HttpResponseRedirect(redirect_to or '/')
    else:
        form = LoginForm()

    info = {
        'form': form,
        'next': redirect_to,
        'site_name': Site.objects.get_current().name,
    }
    if message:
        info['messages'] = [message]
    if error:
        info['reset_error'] = error
    return render(request, 'registration/login.html', info)


def logout(request, next_page=None):
    auth.logout(request)
    return HttpResponseRedirect('/')


def resetpw(request):
    if request.method != 'POST':
        return redirect('login_page')

    email_address = request.POST.get('email_address')
    if not email_address:
        return login_page(request, error='No email address supplied!')

    try:
        user = User.objects.get(email__exact=email_address)
    except User.DoesNotExist:
        return login_page(request, error='Email address not recognised.')
    else:
        new_password = User.objects.make_random_password()
        user.set_password(new_password)
        user.save()

        from django.conf import settings
        admin = settings.ADMINS[0]

        message = '''
        This message is from the PyWeek system. It is in response to
        a request to reset the password in the login "%s".

        The new password is: %s

        Please visit http://pyweek.org/ to log in.

        ---
        PyWeek Admin - %s <%s>
        ''' % (user.username, new_password, admin[0], admin[1])

        send_mail('Your PyWeek login details', cleandoc(message.strip()),
            '%s <%s>' % admin, [email_address])

        return login_page(request, message='Email sent to %s' % email_address)
