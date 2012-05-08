import os
import datetime

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

class FileForm(forms.ModelForm):
    class Meta:
        model = models.File

def entry_upload(request, entry_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge
    errors = {}

    is_member = request.user in entry.users.all()
    if not is_member or not entry.isUploadOpen():
        request.user.message_set.create(message="You're not allowed to upload files!")
        return HttpResponseRedirect('/e/%s/'%entry_id)

    f = FileForm(request.POST, request.FILES)
    info = {
        'challenge': challenge,
        'entry': entry,
        'files': entry.file_set.all(),
        'is_member': True,
        'is_owner': True,
        'form': f,
    }

    # display the form
    if not f.is_valid():
        return render_to_response('challenge/entry_file.html', info,
            context_instance=RequestContext(request))

    # figure where to put the file
    content_file = f.cleaned_data['content']
    content_path = _upload_filepath(challenge, entry, request)
    fspath = os.path.join(MEDIA_ROOT, content_path)

    # make sure the filename is unique
    if os.path.exists(fspath):
        errors.setdefault('content_file', []).append(
            'File already exists with that name')

    # make sure user isn't sneeeky
    is_final = bool(f.cleaned_data['is_final'])
    if is_final and not challenge.isFinalUploadOpen():
        errors.setdefault('is_final', []).append(
            'Final uploads are not allowed now')

    # errors back to the user if any
    # XXX make this better
    data = {}
    if errors:
        return render_to_response('challenge/entry_file.html', info,
            context_instance=RequestContext(request))

    data = _save_upload(challenge, entry, request.user, content_path, request)
    if data:
        # problem creating the thumbnail, so remove that file and tell the user
        # XXX need feedback with custom error "file is not an image"
        os.remove(fspath)
        return render_to_response('challenge/entry_file.html', info,
            context_instance=RequestContext(request))

        # Updated: XXX update for new messages
        # request.user.message_set.create(message='File added!')
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

    # figure where to put the file
    content_path = _upload_filepath(challenge, entry, request)
    fspath = os.path.join(MEDIA_ROOT, content_path)

    if os.path.exists(fspath):
        return HttpResponse('File already exists with that name')

    if _save_upload(challenge, entry, user, content_path, request):
        return HttpResponse('Error: screenshot upload but not an image file')
    else:
        return HttpResponse('File added!')

def _upload_filepath(challenge, entry, request):
    ''' figure where to put the file '''
    entrydir = os.path.join(str(challenge.number), str(entry.name))
    path = os.path.join(MEDIA_ROOT, entrydir)
    if not os.path.exists(path):
        os.makedirs(path)
    return os.path.join(entrydir,
         os.path.basename(request.FILES['content']['filename']))

def _save_upload(challenge, entry, user, content_path, request):
    data = dict(
        challenge = challenge,
        entry = entry,
        user = user,
        created = datetime.datetime.now(models.UTC),
        content = content_path,
        description = html2text(request.POST.get('description', '')),
        is_final = bool(request.POST.get('is_final', False)),
        is_screenshot = bool(request.POST.get('is_screenshot', False)),
        thumb_width = '0',
    )

    fspath = os.path.join(MEDIA_ROOT, content_path)

    # save off uploaded file
    f = open(fspath, 'wb')
    f.write(request.FILES['content']['content'])
    f.close()

    # create screenshot
    if data['is_screenshot']:
        try:
            image = Image.open(fspath)
            image.thumbnail((150, 150), Image.ANTIALIAS)
            data['thumb_width'] = image.size[0]
            image.save(fspath + '-thumb.png', "PNG")
        except:
            return data

    # format / safe-escape the input
    file = models.File(**data)
    file.save()
    if file.is_final:
        entry.has_final = True
        entry.save()
    return None

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
            # Updated: XXX update for new messages
            # request.user.message_set.create(message="File deleted")
            messages.success(request, 'File deleted')
            return HttpResponseRedirect('/e/%s/'%entry_id)
        else:
            # Updated: XXX update for new messages
            # request.user.message_set.create(message="Cancelled")
            messages.success(request, 'Cancelled')
            return HttpResponseRedirect('/e/%s/'%entry_id)

    return render_to_response('confirm.html',
        {
            'url': '/e/%s/delete/%s'%(entry_id, filename),
            'message': 'Are you sure you wish to delete the file %s?'%filename,
        }, context_instance=RequestContext(request))
