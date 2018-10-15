# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.template import loader
from django.shortcuts import render
from django.http import JsonResponse
from .models import Event


PER_PAGE = 10


def timeline(request):
    try:
        before = int(request.GET['before'])
    except (ValueError, KeyError):
        before = None
    try:
        after = int(request.GET['after'])
    except (ValueError, KeyError):
        after = None

    if before:
        events = Event.objects.filter(id__lt=before).order_by('-id')
        num = events.count()
        events = events[:PER_PAGE]
        return render(
            request,
            'activity/timeline-events.html',
            {'timeline': events, 'more': num > PER_PAGE}
        )
    elif after:
        events = Event.objects.filter(id__gt=after).order_by('-id')
        num = events.count()
        top = events[:PER_PAGE]
        html = loader.render_to_string(
            'activity/timeline-events.html',
            {'timeline': top, 'more': False},
            request=request,
        )
        return JsonResponse({
            'num': num,
            'html': html,
        })
    else:
        events = Event.objects.order_by('-id')
        num = events.count()
        return render(request, 'activity/timeline.html', {
            'timeline': events[:PER_PAGE],
            'more': num > PER_PAGE
        })
