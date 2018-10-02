# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django import forms
from django.shortcuts import render
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView
from django.contrib.auth.mixins import PermissionRequiredMixin

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
