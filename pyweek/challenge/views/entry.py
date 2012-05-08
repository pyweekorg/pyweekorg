import cgi, urllib, random, hashlib

from django import forms
from django.contrib import messages
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models
from pyweek import settings
from django.core import validators

from stripogram import html2text, html2safehtml

safeTags = '''b a i br blockquote table tr td img pre p dl dd dt
    ul ol li span div'''.split()


def isUnusedEntryName(field_data):
    if models.Entry.objects.filter(name__exact=field_data):
        raise validators.ValidationError('"%s" already taken'%field_data)
def isUnusedEntryTitle(field_data):
    if models.Entry.objects.filter(title__exact=field_data):
        raise validators.ValidationError('"%s" already taken'%field_data)
def isCommaSeparatedUserList(field_data):
    for name in [e.strip() for e in field_data.split(',')]:
        if not models.User.objects.filter(username__exact=name):
            raise validators.ValidationError('No such user %s'%name)

class AddEntryForm(forms.Form):
    name = forms.CharField(max_length=15, validators=[validators.validate_slug, isUnusedEntryName], required=True)
    title = forms.CharField(required=True, validators=[isUnusedEntryTitle])
    description = forms.CharField(required=False, widget=forms.Textarea)
    users = forms.CharField(validators=[isCommaSeparatedUserList])

def entry_list(request, challenge_id):
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    entries = []
    finished = challenge.isCompFinished()
    all_done = challenge.isAllDone()

    # may rate at all
    may_rate = False
    if not all_done and not request.user.is_anonymous() and challenge.isRatingOpen():
        username = request.user.username
        for e in models.Entry.objects.filter(challenge=challenge_id, users__username__exact=username):
            if e.has_final:
                may_rate = True
                break

    # random sorting per-user
    r = random.random()
    s = int(hashlib.md5(str(request.user)).hexdigest()[:8], 16)
    random.seed(s)

    for entry in models.Entry.objects.filter(challenge=challenge_id):
        if all_done:
            files = []
            found_final = False
            for file in entry.file_set.filter(is_screenshot__exact=False):
                if file.is_final: found_final = True
                elif found_final: break
                files.append(file)
            if not found_final and finished:
                continue
        else:
            files = entry.file_set.filter(is_final__exact=True,
                is_screenshot__exact=False)
            if not files and finished:
                continue

        shots = entry.file_set.filter(is_screenshot__exact=True).order_by("-created")[:1]
        thumb = None
        if shots: thumb = shots[0]

        # generate entry description
        description = entry_description(entry)

        info = {
            'name': entry.name,
            'title': entry.title,
            'description': description,
            'description': description,
            'files': files,
            'sortname': random.random(),
            'may_rate': False,
            'thumb': thumb,
            'num_ratings': len(entry.rating_set.all()),
        }
        if may_rate and finished:
            info['has_rated'] = entry.has_rated(request.user)
        if may_rate and request.user not in entry.users.all():
            info['may_rate'] = True
        entries.append(info)

    # reset random generator
    random.seed(r)

    def sortfun(a, b):
        return cmp(a['sortname'], b['sortname'])
    entries.sort(sortfun)

    # re-sort (yay, stable!) by number of ratings
    def sortfun(a, b):
        return cmp(a['num_ratings'], b['num_ratings'])
    entries.sort(sortfun)

    return render_to_response('challenge/entries.html', {
            'challenge': challenge,
            'entries': entries,
            'limited': finished,
            'finished': finished,
            'all_done': all_done,
        }, context_instance=RequestContext(request))

def entry_description(entry):
    if entry.description:
        description = entry.description + '<br>'
    else:
        description = ''
    e = cgi.escape
    q = urllib.quote
    if entry.is_team():
        users = ', '.join(['<a href="/u/%s">%s</a>'%(q(str(u)), e(str(u)))
           for u in entry.users.all()])
        description += 'This is a team entry consisting of %s.'%users
    else:
        description += 'This is a solo entry by <a href="/u/%s">%s</a>.'%(
            q(str(entry.user)), e(str(entry.user)))
    return description

def entry_add(request, challenge_id):
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    if challenge.isCompFinished():
        if not request.user.is_anonymous():
            request.user.message_set.create(message='Entry registration closed')
        return HttpResponseRedirect("/%s/"%challenge_id)

    if request.POST:
        f = AddEntryForm(request.POST)
        if f.is_valid():
            new_users = []
            if f.cleaned_data['users'].strip():
                for user in [u.strip() for u in f.cleaned_data['users'].split(',')]:
                    new_users.append(models.User.objects.get(username__exact=user).id)
            if request.user.id not in new_users:
                new_users.append(request.user.id)
            entry = models.Entry(name=f.cleaned_data['name'],
                challenge=challenge, user=request.user,
                description=html2safehtml(f.cleaned_data['description'], safeTags),
                title=f.cleaned_data['title'])
            entry.save()
            for u in new_users:
                entry.users.add(u)
            # Updated: XXX need to feedback
            # request.user.message_set.create(message='Entry created!')
            messages.success(request, 'Entry created!')
            return HttpResponseRedirect("/e/%s/"%entry.name)
    else:
        f = AddEntryForm()

    return render_to_response('challenge/entry_add.html',
        {
            'challenge': challenge,
            'form': f,
            'is_member': True,
            'is_owner': True,
        }, context_instance=RequestContext(request))


def entry_display(request, entry_id):
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge
    user_list = entry.users.all()
    is_member = request.user in list(user_list)
    files = entry.file_set.filter(is_screenshot__exact=True).order_by("-created")[:1]
    thumb = None
    if files: thumb = files[0]

    # handle adding the ratings form and accepting ratings submissions
    f = False
    if entry.may_rate(request.user, challenge) and challenge.isRatingOpen():
        errors = {}
        l = entry.rating_set.filter(user__id__exact=request.user.id)
        if len(l):
            # fields for rating editing
            rating = l[0]
            data = rating.__dict__
            manipulator = models.Rating.ChangeManipulator(rating.id)
            for field in manipulator.fields:
                if field.field_name.startswith('created_'):
                    field.is_required=False
            if request.POST:
                new_data = request.POST.copy()
                new_data['entry'] = entry_id
                new_data['user'] = str(request.user.id)
                errors = manipulator.get_validation_errors(new_data)
                if not errors:
                    manipulator.do_html2python(new_data)
                    rating.disqualify = new_data['disqualify']
                    rating.nonworking = new_data['nonworking']
                    rating.fun = new_data['fun']
                    rating.innovation = new_data['innovation']
                    rating.production = new_data['production']
                    rating.comment = html2text(new_data['comment'])
                    rating.save()
                    # Updated: XXX update for new messages
                    #request.user.message_set.create(message='Ratings saved!')
                    messages.info(request, 'Ratings saved!')
                    return HttpResponseRedirect("/e/%s/"%entry.name)
        else:
            data = {}
            # fields for rating entry
            manipulator = models.Rating.AddManipulator()
            for field in manipulator.fields:
                if field.field_name.startswith('created_'):
                    field.is_required=False
            if request.POST:
                new_data = request.POST.copy()
                new_data['entry'] = entry_id
                new_data['user'] = str(request.user.id)
                errors = manipulator.get_validation_errors(new_data)
                if not errors:
                    manipulator.do_html2python(new_data)
                    place = manipulator.save(new_data)
                    # Updated: XXX update for new messages
                    #request.user.message_set.create(message='Ratings saved!')
                    messages.success(request, 'Ratings saved!')
                    return HttpResponseRedirect("/e/%s/"%entry.name)

    rating_results = False
    if challenge.isAllDone() and entry.has_final:
        # display ratings
        d = rating_results = entry.tally_ratings()
        d['dp'] = '%d%%'%(d.get('disqualify', 0)*100)
        d['dnwp'] = '%d%%'%(d.get('nonworking', 0)*100)

    return render_to_response('challenge/entry.html', {
            'challenge': challenge,
            'entry': entry,
            'description': entry_description(entry),
            'files': entry.file_set.all(),
            'thumb': thumb,
            'diary_entries': entry.diaryentry_set.all(),
            'is_user': not request.user.is_anonymous(),
            'is_member': is_member,
            'is_team': len(user_list) > 1,
            'is_owner': entry.user == request.user,
            'form': f,
            'rating': rating_results,
            'awards': entry.entryaward_set.all(),
        }, context_instance=RequestContext(request))


def entry_ratings(request, entry_id):
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge
    anon = request.user.is_anonymous()
    super = not anon and request.user.is_superuser
    if not (challenge.isAllDone() or super):
        if not request.user.is_anonymous():
            request.user.message_set.create(message="You're not allowed to view ratings yet!")
        return HttpResponseRedirect('/e/%s/'%entry_id)
    user_list = entry.users.all()
    is_member = request.user in list(user_list)

    return render_to_response('challenge/entry_ratings.html', {
            'challenge': challenge,
            'entry': entry,
            'is_user': not request.user.is_anonymous(),
            'is_member': is_member,
            'is_team': len(user_list) > 1,
            'is_owner': entry.user == request.user,
        }, context_instance=RequestContext(request))

class EntryForm(forms.Form):
    title = forms.CharField(required=True)
    game = forms.CharField(required=True)
    description = forms.CharField(required=False, widget=forms.Textarea)
    users = forms.CharField(validators=[isCommaSeparatedUserList])

def entry_manage(request, entry_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    if request.user != entry.user:
        request.user.message_set.create(message="You're not allowed to manage this entry!")
        return HttpResponseRedirect('/e/%s/'%entry_id)

    if request.POST:
        f = EntryForm(request.POST)
        if f.is_valid():
            entry.description = html2safehtml(f.cleaned_data['description'], safeTags)
            entry.title = f.cleaned_data['title']
            entry.game = f.cleaned_data['game']
            new_users = []
            for user in [u.strip() for u in f.cleaned_data['users'].split(',')]:
                new_users.append(models.User.objects.get(username__exact=user).id)
            entry.users = new_users
            entry.save()
            message.success(request, 'Changes saved!')
            return HttpResponseRedirect("/e/%s/"%entry_id)
    else:
        f = EntryForm({'name': entry.name, 'title': entry.title,
            'description': entry.description, 'game': entry.game,
            'users': ', '.join(map(str, entry.users.all()))})

    challenge = entry.challenge
    #form = forms.FormWrapper(f, new_data, errors)
    return render_to_response('challenge/entry_admin.html',
        {
            'challenge': challenge,
            'entry': entry,
            'form': f,
            'is_member': True,
            'is_owner': True,
        }, context_instance=RequestContext(request))

