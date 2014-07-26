import os, cgi, urllib, simplejson
import datetime
import xml.sax.saxutils

from PIL import Image

from django import forms
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404, render
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from django.contrib.auth.decorators import login_required
from pyweek.challenge import models
from pyweek import settings
from django.contrib import auth
from django.core import validators
from pyweek.settings import MEDIA_ROOT
from django.db import connection

from stripogram import html2text, html2safehtml

safeTags = '''b a i br blockquote table tr td img pre p dl dd dt
    ul ol li span div'''.split()

class SafeHTMLField(forms.CharField):
    widget = forms.Textarea
    def clean(self, value):
        if '<' in value:
            value = html2safehtml(value, safeTags)
        if not value: raise forms.ValidationError(['This field is required'])
        return value

def index(request):
    return render_to_response('challenge/index.html',
        { } , context_instance=RequestContext(request))

def stats(request):
    return render_to_response('stats.html',
        { } , context_instance=RequestContext(request))

def stats_json(request):
    stats = models.participation()
    json = simplejson.dumps({'stats': stats})
    return HttpResponse(json, mimetype='application/json')

def all_games(request):
    cursor = connection.cursor()
    cursor.execute('''
    SELECT
         auth_user.username as name,
         challenge_entry.name as entry_id
    FROM
         auth_user, challenge_entry, challenge_entry_users
    WHERE
         auth_user.id = challenge_entry_users.user_id AND
         challenge_entry_users.entry_id = challenge_entry.name AND
         challenge_entry.has_final = 1 AND
         challenge_entry.challenge_id < 1000
    ''')
    users = {}
    for name, entry_id in cursor.fetchall():
       users.setdefault(entry_id, []).append(name)
    cursor.execute('''
    SELECT
         challenge_entry.name as entry_id,
         challenge_entry.title as title,
         challenge_entry.game as game,
         challenge_entry.winner_id as winner,
         challenge_entry.challenge_id as challenge_num,
         challenge_ratingtally.overall as rating
    FROM
         challenge_entry
    LEFT OUTER JOIN challenge_ratingtally ON
         (challenge_entry.name = challenge_ratingtally.entry_id)
    WHERE
         challenge_entry.has_final = 1 AND
         challenge_entry.challenge_id < 1000
    ORDER BY
         rating DESC
    ''')
    all = []
    u = urllib.quote
    e = cgi.escape
    for entry_id, title, game, winner, challenge_num, rating in cursor.fetchall():
        team = ',\n'.join(['<a class="small" href="/u/%s">%s</a>'%(u(n), e(n))
            for n in users[entry_id]])
        all.append(dict(entry_id=entry_id, game_name=game or title,
            challenge_num=challenge_num, winner=winner, rating=rating,
            team=team))
    return render_to_response('challenge/all_games.html',
        {
            'all_games': all,
        } , context_instance=RequestContext(request))

def test(request):
    assert False, 'this is false'

def update_has_final(request):
    for entry in models.Entry.objects.all():
        n = len(entry.file_set.filter(is_final__exact=True,
            is_screenshot__exact=False))
        if n:
            entry.has_final = True
            entry.save()
    messages.success(request, 'has_final updated')
    return render_to_response('challenge/index.html',
        {} , context_instance=RequestContext(request))


def challenge_display(request, challenge_id):
    """Display an overview page for a challenge."""
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    screenie = challenge.file_set.order_by('-created').filter(is_screenshot__exact=True)[:0]
    if screenie:
        screenie = screenie[0]

    finished = challenge.isCompFinished()
    all_done = challenge.isAllDone()

    blogposts = models.DiaryEntry.objects.filter(
        entry__challenge__number=challenge.number
    ).select_related('entry').order_by('-created')

    return render_to_response('challenge/display.html',
        {
            'blogposts': blogposts,
            'challenge': challenge,
            'open_polls': challenge.poll_set.filter(is_hidden__exact=False,
                is_open__exact=True),
            'closed_polls': challenge.poll_set.filter(is_hidden__exact=False,
                is_open__exact=False),
            'screenie': screenie,
            'finished': finished and 'finished' or '',
            'all_done': all_done,
            'recent_entryawards': challenge.entryaward_set.all()[:10]
        }, context_instance=RequestContext(request))



def challenge_diaries(request, challenge_id):
    """Display recent blog posts for a challenge."""
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    blogposts = models.DiaryEntry.objects.filter(
        entry__challenge__number=challenge.number
    ).select_related('entry').order_by('-created')

    return render(request, 'challenge/challenge_diaries.html', {
        'blogposts': blogposts,
        'challenge': challenge,
    })


def calculate_rating_tallies(request, challenge_id):
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)
    all_done = challenge.isAllDone()
    if not all_done:
        return HttpResponse('NOT FINISHED')
    challenge.generate_tallies()
    return HttpResponse('DONE')

def fix_winners(request):
    for challenge in models.Challenge.objects.all():
        if challenge.isAllDone():
            challenge.fix_winners()
    return HttpResponse('DONE')

def challenge_ratings(request, challenge_id):
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)
    all_done = challenge.isAllDone()
    individual = []
    team = []
    for rating in models.RatingTally.objects.filter(challenge=challenge).order_by('-overall'):
        if rating.individual:
            individual.append(rating)
        else:
            team.append(rating)

    return render_to_response('challenge/ratings.html',
        {
            'challenge': challenge,
            'polls': challenge.poll_set.filter(is_hidden__exact=False),
            'all_done': all_done,
            'individual_ratings': individual,
            'individual_overall': individual[:3],
            'individual_fun': sorted(individual, key=lambda x: x.fun, reverse=True)[:3],
            'individual_inno': sorted(individual, key=lambda x: x.innovation, reverse=True)[:3],
            'individual_prod': sorted(individual, key=lambda x: x.production, reverse=True)[:3],
            'team_ratings': team,
            'team_overall': team[:3],
            'team_fun': sorted(team, key=lambda x: x.fun, reverse=True)[:3],
            'team_inno': sorted(team, key=lambda x: x.innovation, reverse=True)[:3],
            'team_prod': sorted(team, key=lambda x: x.production, reverse=True)[:3],
        }, context_instance=RequestContext(request))
