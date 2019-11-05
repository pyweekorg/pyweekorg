"""REST API views, primarily for the 'pyweek' CLI tool."""
import posixpath
from urlparse import urljoin

from django.db import models as md
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse

from .. import models


def challenge_downloads(request, challenge_id):
    """Get a view of all downloads for the challenge."""
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)
    all_done = challenge.isAllDone()
    if not all_done:
        resp = {}
    entries = (
        models.Entry.objects.filter(
            challenge__number=challenge_id,
            has_final=True,
        )
        .prefetch_related(
            md.Prefetch(
                'file_set',
                queryset=models.File.objects.filter(
                    is_final=True,
                    is_screenshot=False,
                )
            )
        )
    )
    resp = {
        e.game or e.title: [
            {
                'name': posixpath.basename(f.content.name),
                'url': f.content.url,
                'size': f.content.size,
            }
            for f in e.file_set.all()
        ]
        for e in entries
    }
    return JsonResponse(resp)
