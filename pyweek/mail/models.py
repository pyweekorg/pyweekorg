# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models


class EmailTemplate(models.Model):
    """A template for competition announcements."""
    name = models.SlugField()
    subject = models.CharField(max_length=255)
    body = models.TextField()

    def __str__(self):
        return '<{}: "{}">'.format(self.name, self.subject)


class DraftEmail(models.Model):
    """A draft e-mail announcement to users."""
    list_name = models.CharField(max_length=32)
    subject = models.CharField(max_length=255)
    body = models.TextField()
    edited = models.DateTimeField(auto_now=True)
    sent = models.DateTimeField(null=True)

    status = models.IntegerField(choices=[
        (1, 'Draft'),
        (2, 'Sending'),
        (3, 'Sent'),
    ])

    def __str__(self):
        return '<{self.list_name}: "{self.subject}">'.format(self=self)
