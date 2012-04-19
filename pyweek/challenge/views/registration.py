import smtplib

from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django import forms 
from django.core.mail import send_mail
from django.core.validators import RequiredIfOtherFieldsGiven
from django.contrib.auth.forms import AuthenticationForm
#from django.models.auth import users
from django.contrib.sites.models import Site
from django.contrib import auth

class RegistrationManipulator(forms.Manipulator):
    def __init__(self):
        self.fields = (
            forms.TextField(field_name="name", length=15,
                maxlength=15, is_required=True),
            forms.EmailField(field_name="email", is_required=True),
            forms.PasswordField(field_name="password", length=15),
            forms.PasswordField(field_name="again", length=15,
                validator_list=[RequiredIfOtherFieldsGiven(['password'])]),
        )


def register(request):
    manipulator = RegistrationManipulator()
    redirect_to = request.REQUEST.get('next', '')
    if request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            if not new_data['password']:
                errors['password'] = ['This field is required.']
            if new_data['password'] != new_data['again']:
                errors['again'] = ['Does not match password.']
            if User.objects.filter(username__exact=new_data['name']):
                errors['name'] = ['Username already registered']
            if User.objects.filter(email__exact=new_data['email']):
                errors['email'] = ['Email address already registered']
            if not errors:
                user = User(username=new_data['name'],
                    email=new_data['email'], is_active=True,
                    is_superuser=False, is_staff=False)
                user.set_password(new_data['password'])
                user.save()
                request.session[auth.SESSION_KEY] = user.id
                user.message_set.create(message='Welcome to the Challenge!')
                return HttpResponseRedirect(redirect_to or '/')
    else:
        errors = new_data = {}
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('registration/register.html', {'form': form},
        context_instance=RequestContext(request))


def profile(request):
    manipulator = RegistrationManipulator()
    redirect_to = request.REQUEST.get('next', '')
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    elif request.POST:
        new_data = request.POST.copy()
        errors = manipulator.get_validation_errors(new_data)
        if not errors:
            manipulator.do_html2python(new_data)
            if new_data['password'] != new_data['again']:
                errors['again'] = ['Does not match password.']
            if not errors:
                request.user.username = new_data['name']
                request.user.email = new_data['email']
                if new_data['password']:
                    request.user.set_password(new_data['password'])
                request.user.save()
                request.user.message_set.create(message='Changes saved!')
                return HttpResponseRedirect(redirect_to or '/')
    else:
        errors = {}
        new_data = {
            'name': request.user.username,
            'email': request.user.email,
        }
    form = forms.FormWrapper(manipulator, new_data, errors)
    return render_to_response('registration/profile.html', {'form': form},
        context_instance=RequestContext(request))

def login_page(request, message=None, error=None):
    "Displays the login form and handles the login action."
    manipulator = AuthenticationForm(request)
    redirect_to = request.REQUEST.get('next', '')
    if not (message or error) and request.POST:
        request.session.delete_test_cookie()
        username = request.POST['username']
        password = request.POST['password']
        user = auth.authenticate(username=username, password=password)
        if user is not None:
            if user.is_active:
                auth.login(request, user)
                return HttpResponseRedirect(redirect_to or '/')
            else:
                error = "account disabled"
        else:
            # Return an 'invalid login' error message.    
            error = "invalid login"
            errors = {}
            #return HttpResponseRedirect(redirect_to or '/login/')
    else:
        errors = {}
    request.session.set_test_cookie()
    info = {
        'form': forms.FormWrapper(manipulator, request.POST, errors),
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

