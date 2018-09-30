# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.contrib import admin

from . import models


class EmailTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'subject']


admin.site.register(models.EmailTemplate, EmailTemplateAdmin)
