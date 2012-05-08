
import os
import datetime
import StringIO

from PIL import Image

from django import forms
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models
from pyweek import settings
from pyweek.settings import MEDIA_ROOT

from stripogram import html2text

def view_all_awards(request):
    awards = models.Award.objects.all()
    return render_to_response('challenge/all_awards.html', dict(
        awards=awards,
        ), context_instance=RequestContext(request))

def view_award(request, award_id):
    award = get_object_or_404(models.Award, pk=award_id)
    entry_awards = award.entryaward_set.filter(challenge__number__lt=1000)
    entries = [e.entry for e in entry_awards]
    return render_to_response('challenge/award.html', dict(
        award=award,
        entries=entries,
        ), context_instance=RequestContext(request))

def upload_award(request, entry_id):
    creator = request.user

    if creator.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge

    is_member = creator in entry.users.all()
    if is_member:
        creator.message_set.create(
            message='You cannot give an award to your own entry!')
        return HttpResponseRedirect('/e/%s/'%entry_id)


    info = dict(
        challenge=challenge,
        entry=entry,
        awards=creator.award_set.all(),
    )
    errors = None

    # Display form
    if not (request.POST or request.FILES):
        manipulator = models.Award.AddManipulator()
        for field in manipulator.fields:
            if field.field_name.startswith('created_'):
                field.is_required=False
        info['form'] = forms.FormWrapper(manipulator, {}, {})
        return render_to_response('challenge/upload_award.html', info,
            context_instance=RequestContext(request))

    new_data = dict(
        challenge=challenge.number,
        entry=entry_id,
        creator=creator.id,
        created=datetime.datetime.now(models.UTC),
        content_file=request.FILES.get('content_file', None),
        description=request.POST.get('description', ''),
    )
    if 'award' not in request.POST:
        manipulator = models.Award.AddManipulator()
        for field in manipulator.fields:
            if field.field_name.startswith('created_'):
                field.is_required=False
        errors = manipulator.get_validation_errors(new_data)

    if 'content_file' in request.FILES:
        # figure where to put the file
        content_file = request.FILES['content_file']
        content_path = _upload_filepath(creator, content_file)
        fspath = os.path.join(MEDIA_ROOT, content_path)

        # make sure the filename is unique
        if os.path.exists(fspath):
            errors.setdefault('content_file', []).append(
                'You have already uploaded an award image with that filename')

        # Check dimensions of image
        if not _award_image_ok(content_file['content']):
            errors.setdefault('content_file', []).append(
                'The image could not be read or is not 64x64')

    # errors back to the user if any
    if errors:
        info['form'] = forms.FormWrapper(manipulator, new_data, errors)
        info['errors'] = errors
        return render_to_response('challenge/upload_award.html', info,
            context_instance=RequestContext(request))

    if 'award' in request.POST:
        award = models.Award.objects.get(pk=request.POST['award'])
    else:
        award = _create_award(creator, content_path, request)

    if _give_award(challenge, creator, entry, award):
        messages.success(request, 'Award given!')
    else:
        messages.error(request, 'This entry already has that award.')

    return HttpResponseRedirect('/e/%s/'%entry_id)

def _upload_filepath(user, content_file):
    rel_path = os.path.join('awards', str(user.id))
    path = os.path.join(MEDIA_ROOT, rel_path)
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(rel_path, os.path.basename(content_file['filename']))

def _award_image_ok(content):
    file = StringIO.StringIO(content)
    try:
        image = Image.open(file)
        if image.size == (64, 64):
            return True
    except:
        pass
    return False

def _create_award(user, content_path, request):
    fspath = os.path.join(MEDIA_ROOT, content_path)

    # Write award image to disk
    f = open(fspath, 'wb')
    f.write(request.FILES['content_file']['content'])
    f.close()

    award = models.Award(
        creator=user,
        content=content_path,
        created=datetime.datetime.now(models.UTC),
        description=html2text(request.POST.get('description', ''))
    )
    award.save()
    return award

def _give_award(challenge, user, entry, award):
    # Don't do anything if award has already been given.
    if models.EntryAward.objects.filter(award=award, entry=entry).count():
        return False

    entryaward = models.EntryAward(
        challenge=challenge,
        creator=user,
        entry=entry,
        award=award,
        created=datetime.datetime.now(models.UTC))
    entryaward.save()

    return True

