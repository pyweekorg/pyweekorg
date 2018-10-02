# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models
from django.core.urlresolvers import reverse

from .lists import LISTS
import html2text


class DraftEmail(models.Model):
    """A draft e-mail announcement to users."""
    list_name = models.CharField(max_length=32)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    edited = models.DateTimeField(auto_now=True, editable=False)
    sent = models.DateTimeField(null=True, editable=False)

    STATUS_DRAFT = 1
    STATUS_SENDING = 2
    STATUS_SENT = 3

    status = models.IntegerField(
        choices=[
            (STATUS_DRAFT, 'Draft'),
            (STATUS_SENDING, 'Sending'),
            (STATUS_SENT, 'Sent'),
        ], editable=False,
        default=STATUS_DRAFT,
    )

    @property
    def list_title(self):
        """Get the title of the recipients list."""
        name, list_func = LISTS[self.list_name]
        return name

    @property
    def recipients(self):
        """Get a QuerySet of recipient EmailAddresses."""
        name, list_func = LISTS[self.list_name]
        return list_func()

    @property
    def list_reason(self):
        """Get a description of why the user was e-mailed.

        These reasons are required to start with 'because ' and end with
        a '.'. They may contain HTML.

        """
        name, list_func = LISTS[self.list_name]
        return list_func.reason

    def body_text(self):
        """Convert the HTML body to text."""
        converter = html2text.HTML2Text()
        converter.inline_links = False
        return converter.handle(self.body)

    def __str__(self):
        return '<{self.list_name}: "{self.subject}">'.format(self=self)

    def get_absolute_url(self):
        """Get a URL to preview the e-mail."""
        return reverse('preview-email', args=(self.id,))
