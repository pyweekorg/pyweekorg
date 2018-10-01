from inspect import cleandoc

from django.contrib.auth.models import User
from django.shortcuts import render, redirect
from django.template import RequestContext
from django.http import HttpResponseRedirect, HttpResponseForbidden
from django import forms
from django.forms.models import inlineformset_factory
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.contrib import auth, messages
from django.contrib.auth.decorators import login_required

from snowpenguin.django.recaptcha2.fields import ReCaptchaField
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget

from ..forms import LoginForm
from ..models import Challenge
from ...users.models import EmailAddress, UserSettings


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


class ProfileForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        exclude = ['user']


class PasswordForm(forms.ModelForm):
    old_password = forms.CharField(widget=forms.PasswordInput, required=False)
    password = forms.CharField(widget=forms.PasswordInput, required=False)
    again = forms.CharField(widget=forms.PasswordInput, required=False)

    class Meta:
        model = User
        fields = []

    def clean_old_password(self):
        pw = self.cleaned_data['old_password']
        if not pw:
            return None
        if not self.instance.check_password(pw):
            raise forms.ValidationError(
                "This password is not correct."
            )
        return pw

    def clean(self):
        if not any(self.cleaned_data.values()):
            return {}
        if not self.cleaned_data['old_password']:
            raise forms.ValidationError(
                "You must enter the old password."
            )
        if not self.cleaned_data['password'] and not self.cleaned_data['again']:
            raise forms.ValidationError(
                "You must enter the new password."
            )
        if self.cleaned_data['password'] != self.cleaned_data['again']:
            raise forms.ValidationError(
                "Supplied passwords did not match."
            )

    def save(self):
        if not self.cleaned_data:
            return

        if self.cleaned_data['password'] and self.cleaned_data['old_password']:
            messages.success(
                self.request,
                'Your password has been updated.'
            )
            self.instance.set_password(self.cleaned_data['password'])
            self.instance.save()
            auth.login(self.request, self.request.user)


class AddressForm(forms.ModelForm):
    address = forms.CharField(
        widget=forms.TextInput(attrs={'size': '50'}),
        required=False
    )

    class Meta:
        model = EmailAddress
        fields = ['address']


    def save(self):
        new_address = self.cleaned_data['address']
        if not new_address:
            return
        obj, created = EmailAddress.objects.get_or_create(
            user=self.user,
            address=new_address,
        )
        if created:
            obj.request_verification()
            messages.success(
                self.request,
                'Your new e-mail address, {}, must be '.format(new_address) +
                'verified. Please check your e-mail for a verification link.'
            )


def _handle_delete_address(request):
    to_delete = request.POST.get('delete-address')
    if not to_delete:
        return

    if to_delete == request.user.email:
        messages.error(
            request,
            'Your primary e-mail address can not be deleted.'
        )

    try:
        addr = request.user.emailaddress_set.get(address=to_delete)
    except EmailAddress.DoesNotExist:
        pass
    else:
        addr.delete()
        messages.success(
            request,
            'E-mail address {} has been deleted.'.format(to_delete)
        )


def _handle_make_primary(request):
    to_make_primary = request.POST.get('make-primary-address')
    if not to_make_primary:
        return

    try:
        addr = request.user.emailaddress_set.get(address=to_make_primary)
    except EmailAddress.DoesNotExist:
        return

    if not addr.verified:
        messages.error(
            request,
            'You can not set your primary e-mail to an unverified e-mail '
            'address.'
        )
        return

    user = request.user
    user.email = addr.address
    user.save()
    messages.success(
        request,
        'Your primary e-mail address has been set to {}.'.format(addr.address)
    )


def _handle_resend_verification(request):
    to_resend = request.POST.get('resend-verification')
    if not to_resend:
        return

    try:
        addr = request.user.emailaddress_set.get(address=to_resend)
    except EmailAddress.DoesNotExist:
        return

    if addr.verified:
        messages.error(
            request,
            'Your e-mail address {} is already verified.'.format(addr.address)
        )
        return

    addr.request_verification()
    messages.success(
        request,
        'Please check your e-mail for a verification link.'
    )


@login_required
def profile(request):
    def create_forms(data=None):
        profile_form = ProfileForm(
            data,
            prefix='profile',
            instance=request.user.settings,
        )
        password_form = PasswordForm(
            data,
            prefix='passwd',
            instance=request.user
        )
        address_form = AddressForm(data, prefix='addr')
        address_form.user = request.user

        forms = profile_form, password_form, address_form
        for f in forms:
            f.request = request
        return forms

    if request.POST:
        _handle_delete_address(request)
        _handle_make_primary(request)
        _handle_resend_verification(request)
        forms = create_forms(request.POST)
        if all(f.is_valid() for f in forms):
            for f in forms:
                f.save()
            return HttpResponseRedirect(request.path)
    else:
        forms = create_forms()

    profile_form, password_form, address_form = forms
    return render(
        request,
        'registration/profile.html',
        {
            'addresses': request.user.emailaddress_set.all(),
            'profile_form': profile_form,
            'password_form': password_form,
            'address_form': address_form,
        }
    )

    if request.POST:
        _handle_delete_address(request)
        forms = create_forms(request.POST)
        if all(f.is_valid() for f in forms):
            for f in forms:
                f.save()
            messages.success(request, 'Changes saved!')
            return HttpResponseRedirect(request.path)
    else:
        forms = create_forms()

    profile_form, password_form, address_form = forms
    return render(
        request,
        'registration/profile.html',
        {
            'addresses': request.user.emailaddress_set.all(),
            'profile_form': profile_form,
            'password_form': password_form,
            'address_form': address_form,
        }
    )



@login_required
def verify_email(request):
    """Verify an e-mail address."""
    try:
        key = request.GET['key']
    except KeyError:
        return HttpResponseRedirect('/profile/')

    try:
        address = EmailAddress.objects.get(verification_key=key)
    except EmailAddress.DoesNotExist:
        messages.error(request, 'Invalid verification key')
        return HttpResponseRedirect('/profile/')

    if address.verified:
        messages.warning(
            request,
            'Your e-mail address has already been verified.'
        )
    else:
        address.verified = True
        address.save()
        messages.success(
            request,
            'Your e-mail address {} has been verified.'.format(address.address)
        )
    return HttpResponseRedirect('/profile/')


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
        return redirect(login_page)

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
