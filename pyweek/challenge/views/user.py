from django import newforms
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models

from stripogram import html2text, html2safehtml

safeTags = '''b a i br blockquote table tr td img pre p dl dd dt
    ul ol li span div'''.split()

class SafeHTMLField(newforms.CharField):
    widget = newforms.Textarea
    def clean(self, value):
        if '<' in value:
            value = html2safehtml(value, safeTags)
        if not value: raise newforms.ValidationError(['This field is required'])
        return value


def user_display(request, user_id):
    user = get_object_or_404(models.User, username=user_id)

    entries = models.Entry.objects.filter(
        challenge__number__lt=1000, users=user)
    given_awards = user.award_set.all()
    received_awards = models.EntryAward.objects.filter(
        challenge__number__lt=1000, entry__users=user)
    return render_to_response('challenge/user_display.html',
        {
            'profile_user': user,
            'entries': entries,
            'given_awards': given_awards,
            'received_awards': received_awards,
        }, context_instance=RequestContext(request))

class ProfileForm(newforms.Form):
    content = SafeHTMLField(label='Text to appear on your profile page',
        help_text='Basic HTML tags allowed: %s'%(', '.join(safeTags)))

def profile_description(request):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')

    profile = request.user.userprofile_set.all()
    if profile:
        profile = profile[0]
        data = {'content': profile.content}
    else:
        data = {}
        profile = None

    if request.POST:
        form = ProfileForm(request.POST)
        if form.is_valid():
            content = form.clean_data['content']

            # do the save
            if profile is None:
                profile = models.UserProfile(content=content, user=request.user)
            else:
                profile.content = content
            profile.save()
            request.user.message_set.create(message='Description saved!')
            return HttpResponseRedirect('/profile_description/')
    else:
        form = ProfileForm(data)
    return render_to_response('challenge/profile_description.html',
        {
            'form': form,
        }, context_instance=RequestContext(request))

