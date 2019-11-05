import os
import datetime

from PIL import Image

from django import forms
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models
from pyweek import settings
from pyweek.settings import MEDIA_ROOT
from pyweek.activity.models import log_event

from stripogram import html2text


class FileForm(forms.Form):
    content = forms.FileField()
    description = forms.CharField(max_length=255)
    is_final = forms.BooleanField(required=False)
    is_screenshot = forms.BooleanField(required=False)

def entry_upload(request, entry_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge

    is_member = request.user in entry.users.all()
    if not is_member or not entry.isUploadOpen():
        messages.error(request, "You're not allowed to upload files!")
        return HttpResponseRedirect('/e/%s/'%entry_id)

    if request.method == 'POST':
        f = FileForm(request.POST, request.FILES)
    else:
        f = FileForm()

    info = {
        'challenge': challenge,
        'entry': entry,
        'files': entry.file_set.all(),
        'is_member': True,
        'is_owner': entry.user == request.user,
        'form': f,
    }

    # just display the form?
    if not f.is_valid():
        return render(request, 'challenge/entry_file.html', info)

    # make sure user isn't sneeeky
    if f.cleaned_data['is_final'] and not challenge.isFinalUploadOpen():
        f._errors['is_final'] = f.error_class(["Final uploads are not allowed now."])
        return render(request, 'challenge/entry_file.html', info)

    # avoid dupes
    if os.path.exists(os.path.join(MEDIA_ROOT, str(challenge.number), entry.name,
            request.FILES['content'].name)):
        f._errors['content'] = f.error_class(["File with that filename already exists."])
        return render(request, 'challenge/entry_file.html', info)

    file = models.File(
        challenge=challenge,
        entry=entry,
        user=request.user,
        created=datetime.datetime.utcnow(),
        content=request.FILES['content'],
        description=html2text(f.cleaned_data['description']),
        is_final=f.cleaned_data['is_final'],
        is_screenshot=f.cleaned_data['is_screenshot'],
        thumb_width=0,
    )
    file.save()
    if file.is_final:
        entry.has_final = True
        entry.save()

    if file.is_screenshot:
        try:
            _make_thumbnail(file)
        except IOError as e:
            # XXX need feedback with custom error "file is not an image"
            msg = e.args[0]
            if not e.startswith('cannot identify image file'):
                raise
	    messages.error(request, 'File is not an image')
            return render(request, 'challenge/entry_file.html', info)

        log_event(
            type='new-screenshot',
            user=request.user,
            target=file,
            challenge=challenge.number,
            game=entry.display_title,
            name=entry.name,
            description=file.description,
            role=file.get_image_role(),
        )

    messages.success(request, 'File added!')
    return HttpResponseRedirect('/e/%s/'%entry_id)


def oneshot_upload(request, entry_id):
    entry = models.Entry.objects.filter(name__exact=entry_id)
    if not entry: return HttpResponse('Invalid entry *short* name')
    entry = entry[0]
    challenge = entry.challenge

    version = int(request.POST.get('version', '1'))
    if version < 2:
        return HttpResponse('Please update your pyweek-upload.py script')

    data = request.POST
    user = request.POST.get('user', '')
    if not user: return HttpResponse('Invalid login')

    user = models.User.objects.filter(username__exact=user)
    if not user: return HttpResponse('Invalid login')
    user = user[0]

    password = request.POST.get('password', '')
    if not user.check_password(password):
        return HttpResponse('Invalid login')

    # check authorisation
    if not user in entry.users.all() or not entry.isUploadOpen():
        return HttpResponse("You're not allowed to upload files!")

    # make sure user isn't sneeeky
    is_final = bool(request.POST.get('is_final', False)),
    if is_final and not challenge.isFinalUploadOpen():
        return HttpResponse('Final uploads are not allowed now')

    # avoid dupes
    if os.path.exists(os.path.join(MEDIA_ROOT, str(challenge.number), entry.name,
            request.FILES['content_file'].name)):
        return HttpResponse('File with that filename already exists.')

    upload_file = request.FILES['content_file']
    file = models.File(
        challenge=challenge,
        entry=entry,
        user=user,
        created=datetime.datetime.now(models.UTC),
        content=upload_file,
        description=html2text(data.get('description', '')),
        is_final=bool(data.get('is_final', False)),
        is_screenshot=bool(data.get('is_screenshot', False)),
        thumb_width=0,
    )
    file.save()
    if file.is_final:
        entry.has_final = True
        entry.save()

    if data['is_screenshot']:
        try:
            _make_thumbnail(upload_file)
        except IOError as e:
            return HttpResponse(
                'Error uploading screenshot: {}'.format(e)
            )
    return HttpResponse('File added!')


import io
import posixpath
from django.core.files.storage import get_storage_class


def _make_thumbnail(file):
    image = Image.open(io.BytesIO(file.content.read()))
    image.thumbnail((150, 150), Image.ANTIALIAS)
    target = file.content.name + '-thumb.png'

    storage = get_storage_class()
    with storage().open(target, 'wb') as f:
        image.save(f, "PNG")
    file.thumb_width = image.size[0]
    file.save()


def file_delete(request, entry_id, filename):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge_id = entry.challenge_id

    is_member = request.user in entry.users.all()
    if not is_member:
        messages.error(request, "You're not allowed to delete files!")
        return HttpResponseRedirect('/e/%s/'%entry_id)

    if request.method == 'POST':
        if request.POST.get('confirm', ''):
            try:
                ob = entry.file_set.filter(content__exact=filename)[0]
            except (models.File.DoesNotExist, IndexError):
                pass
            else:
                filename = ob.content.name
                ob.content.delete()
                ob.delete()

                storage = get_storage_class()()
                storage.delete(filename + '-thumb.png')

                messages.success(request, 'File deleted')
                return HttpResponseRedirect('/e/%s/'%entry_id)
        else:
            messages.success(request, 'Cancelled')
            return HttpResponseRedirect('/e/%s/'%entry_id)

    return render(request, 'confirm.html',
        {
            'url': '/e/%s/delete/%s'%(entry_id, filename),
            'message': 'Are you sure you wish to delete the file %s?'%filename,
        }
    )

