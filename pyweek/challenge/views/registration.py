import smtplib

from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django import forms
from django.core.mail import send_mail
from django.contrib.auth.forms import AuthenticationForm
#from django.models.auth import users
from django.contrib.sites.models import Site
from django.contrib import auth, messages


class RegistrationForm(forms.Form):
    name = forms.CharField(max_length=15, required=True)
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.PasswordInput)
    again = forms.CharField(widget=forms.PasswordInput)


def register(request):
    redirect_to = request.REQUEST.get('next', '')
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
                user = User.objects.create_user(f.cleaned_data['name'],
                    f.cleaned_data['email'], f.cleaned_data['password'])
                auth.login(request, user)
                messages.info(request, 'Welcome to the Challenge!')
                return HttpResponseRedirect(redirect_to or '/')
    else:
        f = RegistrationForm()
    return render_to_response('registration/register.html', {'form': f},
        context_instance=RequestContext(request))


def profile(request):
    redirect_to = request.REQUEST.get('next', '')
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
        errors = {}
        f = RegistrationForm({
            'name': request.user.username,
            'email': request.user.email,
        })
    return render_to_response('registration/profile.html', {'form': f},
        context_instance=RequestContext(request))

def login_page(request, message=None, error=None):
    "Displays the login form and handles the login action."
    redirect_to = request.REQUEST.get('next', '')
    if request.POST:
        # Oh, Django, you are shitting me...
        f = AuthenticationForm(data=request.POST)
    else:
        f = AuthenticationForm()
    if not (message or error) and request.POST and f.is_valid():
        request.session.delete_test_cookie()
        username = f.cleaned_data['username']
        password = f.cleaned_data['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            auth.login(request, user)
            return HttpResponseRedirect(redirect_to or '/')
        else:
            # Return an 'invalid login' error message.
            error = "invalid login"
    request.session.set_test_cookie()
    info = {
        'form': f,
        'next': redirect_to,
        'site_name': Site.objects.get_current().name,
    }
    if message:
        info['messages'] = [message]
    if error:
        info['reset_error'] = error
    return render_to_response('registration/login.html', info,
        context_instance=RequestContext(request))

def logout(request, next_page=None):
    auth.logout(request)
    return HttpResponseRedirect('/')

def resetpw(request):
    email_address = request.REQUEST['email_address']
    if not email_address:
        return login_page(request, error='No email address supplied!')
    try:
        user = User.objects.get(email__exact=email_address)
    except User.DoesNotExist:
        return login_page(request, error='Email address not recognised!')
    new_password = User.objects.make_random_password()
    user.set_password(new_password)
    user.save()

    from django.conf import settings
    admin = settings.ADMINS[0]

    message = '''This message is from the PyWeek system. It is in response to
a request to reset the password in the login "%s".

The new password is: %s

Please visit http://pyweek.org/ to log in.

---
PyWeek Admin - %s <%s>
'''%(user.username, new_password, admin[0], admin[1])

    send_mail('Your PyWeek login details', message,
        '%s <%s>'%admin, [email_address])

    return login_page(request, message='Email sent to %s'%email_address)

