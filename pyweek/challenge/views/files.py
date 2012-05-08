import os
import datetime

from PIL import Image

from django import forms
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models
from pyweek import settings
from pyweek.settings import MEDIA_ROOT

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
        request.user.message_set.create(message="You're not allowed to upload files!")
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
        'is_owner': True,
        'form': f,
    }

    # just display the form?
    if not f.is_valid():
        return render_to_response('challenge/entry_file.html', info,
            context_instance=RequestContext(request))

    # make sure user isn't sneeeky
    if f.cleaned_data['is_final'] and not challenge.isFinalUploadOpen():
        f._errors['is_final'] = f.error_class(["Final uploads are not allowed now."])
        return render_to_response('challenge/entry_file.html', info,
            context_instance=RequestContext(request))

    # avoid dupes
    if os.path.exists(os.path.join(MEDIA_ROOT, str(challenge.number), entry.name,
            request.FILES['content'].filename)):
        f._errors['content'] = f.error_class(["File with that filename already exists."])
        return render_to_response('challenge/entry_file.html', info,
            context_instance=RequestContext(request))

    file = models.File(
        challenge=challenge,
        entry=entry,
        user=request.user,
        created=datetime.datetime.now(models.UTC),
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
        except:
            # XXX need feedback with custom error "file is not an image"
            return render_to_response('challenge/entry_file.html', info,
                context_instance=RequestContext(request))

    # XXX update for new messages
    # request.user.message_set.create(message='File added!')
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
            request.FILES['content'].filename)):
        return HttpResponse('File with that filename already exists.')

    file = models.File(
        challenge=challenge,
        entry=entry,
        user=user,
        created=datetime.datetime.now(models.UTC),
        content=request.FILES['content_file'],
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
            _make_thumbnail(file)
        except:
            return HttpResponse('Error: screenshot upload but not an image file')
    return HttpResponse('File added!')

def _make_thumbnail(file):
    image = Image.open(file.content.path)
    image.thumbnail((150, 150), Image.ANTIALIAS)
    image.save(file.content.path + '-thumb.png', "PNG")
    file.thumb_width = image.size[0]
    file.save()

def file_delete(request, entry_id, filename):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge_id = entry.challenge_id

    is_member = request.user in entry.users.all()
    if not is_member:
        request.user.message_set.create(message="You're not allowed to upload files!")
        return HttpResponseRedirect('/e/%s/'%entry_id)

    if request.POST:
        data = request.POST.copy()
        if data.has_key('confirm'):
            filepath = os.path.join(str(challenge_id), entry.name, filename)
            try:
                ob = entry.file_set.get(content__exact=filepath)
                ob.delete()
            except models.File.DoesNotExist:
                pass
            abspath = os.path.join(MEDIA_ROOT, filepath)
            if os.path.exists(abspath):
                os.remove(abspath)
            if os.path.exists(abspath + '-thumb.png'):
                os.remove(abspath + '-thumb.png')
            # XXX update for new messages
            # request.user.message_set.create(message="File deleted")
            return HttpResponseRedirect('/e/%s/'%entry_id)
        else:
            # XXX update for new messages
            # request.user.message_set.create(message="Cancelled")
            return HttpResponseRedirect('/e/%s/'%entry_id)

    return render_to_response('confirm.html',
        {
            'url': '/e/%s/delete/%s'%(entry_id, filename),
            'message': 'Are you sure you wish to delete the file %s?'%filename,
        }, context_instance=RequestContext(request))
