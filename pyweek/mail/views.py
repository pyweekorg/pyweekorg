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

from .lists import LISTS
from .models import DraftEmail
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
