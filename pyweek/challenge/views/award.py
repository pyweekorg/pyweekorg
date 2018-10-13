
import os
import datetime
import StringIO

from PIL import Image

from django import forms
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models
from pyweek import settings
from pyweek.settings import MEDIA_ROOT

from stripogram import html2text

def view_all_awards(request):
    awards = models.Award.objects.all()
    return render(request, 'challenge/all_awards.html', {'awards': awards})


def view_award(request, award_id):
    award = get_object_or_404(models.Award, pk=award_id)
    entry_awards = award.entryaward_set.filter(challenge__number__lt=1000)
    entries = [e.entry for e in entry_awards]
    return render(
        request, 'challenge/award.html', dict(
            award=award,
            entries=entries,
        )
    )


class GiveAwardForm(forms.Form):
    award = forms.ModelChoiceField(queryset=None)

    def __init__(self, user, *args, **kwargs):
        super(GiveAwardForm, self).__init__(*args, **kwargs)
        self.user = user
        self.fields['award'].queryset = user.award_set.all()


def give_award(request, entry_id):
    creator = request.user

    if creator.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge

    is_member = creator in entry.users.all()
    if is_member:
        messages.error(request, 'You cannot give an award to your own entry!')
        return HttpResponseRedirect('/e/%s/'%entry_id)

    info = dict(
        challenge=challenge,
        entry=entry,
        awards=creator.award_set.all(),
        upload_form=UploadAwardForm(),
    )
    errors = None

    # Display form
    if request.method != 'POST':
        f = GiveAwardForm(creator)
        info['give_form'] = f
        return render(request, 'challenge/upload_award.html', info)

    f = GiveAwardForm(creator, request.POST)
    info['give_form'] = f
    if not f.is_valid():
        return render(request, 'challenge/upload_award.html', info)

    if _give_award(challenge, creator, entry, f.cleaned_data['award']):
        messages.success(request, 'Award given!')
    else:
        messages.error(request, 'This entry already has that award.')

    return HttpResponseRedirect('/e/%s/'%entry_id)

class UploadAwardForm(forms.Form):
    content = forms.FileField()
    description = forms.CharField(max_length=255)

def upload_award(request, entry_id):
    creator = request.user

    if creator.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge

    is_member = creator in entry.users.all()
    if is_member:
        messages.error(request, 'You cannot give an award to your own entry!')
        return HttpResponseRedirect('/e/%s/'%entry_id)

    info = dict(
        challenge=challenge,
        entry=entry,
        awards=creator.award_set.all(),
        give_form=GiveAwardForm(creator),
    )
    errors = None

    if request.method == 'POST':
        f = UploadAwardForm(request.POST, request.FILES)
    else:
        f = UploadAwardForm()
    info['upload_form'] = f

    # Display form
    if not f.is_valid():
        return render(request, 'challenge/upload_award.html', info)

    # make sure the filename is unique
#    if os.path.exists(fspath):
#        error = 'You have already uploaded an award image with that filename.'

    # check dimensions of image
    ok = False
    try:
        image = Image.open(request.FILES['content'])
        if image.size == (64, 64):
            ok = True
    except:
        pass
    if not ok:
        messages.error(request, 'The image could not be read or is not 64x64')
        return render(request, 'challenge/upload_award.html', info)

    # Write award image to disk
    award = models.Award(creator=creator,
        content=request.FILES['content'],
        description=html2text(f.cleaned_data['description']),
    )
    award.save()

    if _give_award(challenge, creator, entry, award):
        messages.success(request, 'Award given!')
    else:
        messages.error(request, 'This entry already has that award.')

    return HttpResponseRedirect('/e/%s/'%entry_id)

def _give_award(challenge, user, entry, award):
    # Don't do anything if award has already been given.
    if models.EntryAward.objects.filter(award=award, entry=entry).count():
        return False

    entryaward = models.EntryAward(challenge=challenge, creator=user,
        entry=entry, award=award)
    entryaward.save()

    return True

