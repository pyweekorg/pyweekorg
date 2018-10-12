# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.shortcuts import render
from .models import Event


def timeline(request):
    events = Event.objects.order_by('-date')[:15]
    return render(request, 'activity/timeline.html', {'timeline': events})
