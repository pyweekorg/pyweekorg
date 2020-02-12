# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from datetime import datetime

from django import forms
from django.conf import settings
from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.decorators import permission_required
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.contrib import messages
from django.core import signing

from ..challenge.views.registration import redirect_to_login
from .lists import LISTS
from .models import DraftEmail
from ..users.models import UserSettings
from . import sending


class DraftEmailList(PermissionRequiredMixin, ListView):
    permission_required = 'mail.add_draftemail'
    model = DraftEmail
    paginate_by = 30

    def get_queryset(self):
        drafts = super(DraftEmailList, self).get_queryset()
        return drafts.filter(status=DraftEmail.STATUS_DRAFT)


class EditEmailForm(forms.ModelForm):
    def list_choices():
        choices = []
        for key, (name, list_func) in LISTS.iteritems():
            num_recips = list_func().count()
            choices.append(
                (key, '{} ({} recipients)'.format(name, num_recips))
            )
        return choices

    list_name = forms.ChoiceField(choices=list_choices)
    subject = forms.CharField(
        widget=forms.TextInput(attrs={'size': '80'}),
    )

    class Meta:
        model = DraftEmail
        fields = ['list_name', 'subject', 'body']


class ComposeEmail(PermissionRequiredMixin, CreateView):
    permission_required = 'mail.add_draftemail'
    model = DraftEmail
    form_class = EditEmailForm


class EditEmail(PermissionRequiredMixin, UpdateView):
    permission_required = 'mail.add_draftemail'
    model = DraftEmail
    form_class = EditEmailForm


class PreviewEmail(PermissionRequiredMixin, DetailView):
    permission_required = 'mail.add_draftemail'
    model = DraftEmail

    def get_context_data(self, **kwargs):
        ctx = super(PreviewEmail, self).get_context_data(**kwargs)
        ctx['subject'] = '[PyWeek] {}'.format(self.object.subject.strip())
        ctx['body_html'] = self.object.body
        ctx['reason'] = self.object.list_reason
        return ctx


class PreviewEmailText(PreviewEmail):
    template_name = 'mail/draftemail_preview_text.html'

    def get_context_data(self, **kwargs):
        ctx = super(PreviewEmailText, self).get_context_data(**kwargs)
        html, text = sending._make_payload(
            self.object.body,
            self.object.list_reason
        )
        ctx['text'] = text
        return ctx


@permission_required('mail.add_draftemail')
def send(request, pk):
    """Send a draft e-mail."""
    if request.method != 'POST':
        return redirect('draft-emails')
    email = get_object_or_404(DraftEmail, pk=pk)
    if email.status != DraftEmail.STATUS_DRAFT:
        messages.error(
            request,
            "This e-mail has already been sent."
        )
        return redirect('draft-emails')

    email.status = DraftEmail.STATUS_SENT
    email.sent = datetime.utcnow()
    email.save()
    try:
        recipients = list(email.recipients.select_related('user'))
        sending.send(
            subject=email.subject,
            html_body=email.body,
            recipients=recipients,
            priority=sending.PRIORITY_LOW,
            reason=email.list_reason,

        )
    except BaseException:
        email.status = DraftEmail.STATUS_DRAFT
        email.save()
        raise
    messages.success(
        request,
        "E-mail '{}' sent to {} recipients".format(
            email.subject,
            len(recipients)
        )
    )
    return redirect('draft-emails')


class SettingsForm(forms.ModelForm):
    class Meta:
        model = UserSettings
        fields = [
            f.name for f in UserSettings._meta.fields
            if f.name.startswith('email_')
        ]


def unsubscribe(request):
    """Show a page letting users unsubscribe from e-mails without logging in.

    Access will be authenticated using a signed token containing the user's
    username.
    """
    try:
        token = request.GET['token']
        user = sending.rot13(sending.UNSUBSCRIBE_SIGNER.unsign(token))
    except (KeyError, signing.BadSignature):
        return redirect_to_login('Missing/invalid unsubscribe token')

    profile = UserSettings.objects.get(user__username=user)

    if request.method == 'POST':
        form = SettingsForm(request.POST, instance=profile)
        if form.is_valid():
            form.save()
            return redirect_to_login(
                "Your e-mail preferences have been saved."
            )
    else:
        form = SettingsForm(instance=profile)

    return render(request, 'mail/unsubscribe.html', {
        'token': token,
        'form': form,
    })
