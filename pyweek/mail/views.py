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
from django.template.loader import render_to_string
from django.template import Context
from mailer import send_html_mail
import mailer.models

from .lists import LISTS
from .models import DraftEmail


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


class PreviewEmailText(PreviewEmail):
    template_name = 'mail/draftemail_preview_text.html'


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

    ctx = {'object': email}
    html_body = render_to_string('mail/admin_email.html', context=ctx)
    text_body = render_to_string('mail/admin_email.txt', context=ctx)

    email.status = DraftEmail.STATUS_SENT
    email.sent = datetime.utcnow()
    email.save()
    recips = 0
    try:
        for addr in email.recipients.select_related('user'):
            to_email = '{} <{}>'.format(addr.user.username, addr.address)

            #TODO: identify sending user rather than using default
            from_email = settings.DEFAULT_FROM_EMAIL
            send_html_mail(
                subject=email.full_subject,
                message=text_body,
                message_html=html_body,
                from_email=from_email,
                recipient_list=[to_email],
                priority=mailer.models.PRIORITY_LOW,
            )
            recips += 1
    except BaseException:
        email.status = DraftEmail.STATUS_DRAFT
        email.save()
        raise
    messages.success(
        request,
        "E-mail '{}' sent to {} recipients".format(email.subject, recips)
    )
    return redirect('draft-emails')
