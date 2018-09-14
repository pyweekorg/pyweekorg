from django import forms
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from pyweek.challenge import models

from stripogram import html2safehtml
import collections

safeTags = '''b a i br blockquote table tr td img pre p dl dd dt
    ul ol li span div'''.split()


class SafeHTMLField(forms.CharField):
    widget = forms.Textarea

    def clean(self, value):
        if '<' in value:
            value = html2safehtml(value, safeTags)
        if not value:
            raise forms.ValidationError(['This field is required'])
        return value


def user_display(request, user_id):
    user = get_object_or_404(models.User, username=user_id)

    entries = models.Entry.objects.filter(
        challenge__number__lt=1000, users=user)
    given_awards = user.award_set.all()
    received_awards = models.EntryAward.objects.filter(
        challenge__number__lt=1000, entry__users=user)
    return render(request, 'challenge/user_display.html',
        {
            'profile_user': user,
            'entries': entries,
            'given_awards': given_awards,
            'received_awards': received_awards,
        }
    )


class ProfileForm(forms.Form):
    content = SafeHTMLField(label='Text to appear on your profile page',
        help_text='Basic HTML tags allowed: %s' % (', '.join(safeTags)))


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
            content = form.cleaned_data['content']

            # do the save
            if profile is None:
                profile = models.UserProfile(content=content,
                    user=request.user)
            else:
                profile.content = content
            profile.save()
            messages.success(request, 'Description saved!')
            return HttpResponseRedirect('/profile_description/')
    else:
        form = ProfileForm(data)
    return render(request, 'challenge/profile_description.html',
        {
            'form': form,
        }
    )


def delete_spammer(request, user_id):
    if not request.POST or not request.user.is_staff:
        return user_display(request, user_id)

    user = models.User.objects.get(username__exact=user_id)
    comments = list(models.DiaryComment.objects.filter(user=user))
    d = collections.defaultdict(list)
    for comment in comments:
        d[comment.diary_entry].append(comment)

    user.password = 'X'
    user.save()

    last = None
    for diary_entry, comments in d.items():
        for comment in diary_entry.diarycomment_set.all():
            if comment.user != user:
                last = comment
        if last is None:
            diary_entry.actor = diary_entry.user
            diary_entry.last_comment = None
            diary_entry.activity = diary_entry.created
            diary_entry.reply_count = 0
        else:
            diary_entry.last_comment = last
            diary_entry.activity = last.created
            diary_entry.actor = last.user
            diary_entry.reply_count -= len(comments)
        diary_entry.save()
        for comment in comments:
            comment.delete()

    messages.success(request, 'Spammer deleted! ({0})'.format(user))
    return HttpResponseRedirect('/u/%s/' % user_id)
