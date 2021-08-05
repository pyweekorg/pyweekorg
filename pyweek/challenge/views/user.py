from django import forms
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponseRedirect
from django.core.validators import RegexValidator
from pyweek.challenge import models

from stripogram import html2safehtml
import collections
from django.core.exceptions import ObjectDoesNotExist

safeTags = '''b a i br blockquote table tr td img pre p dl dd dt
    ul ol li span div'''.split()


class SafeHTMLField(forms.CharField):
    widget = forms.Textarea

    def clean(self, value):
#        if value is None:
#            return None
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

    possible_spammer = entries.filter(has_final=True).count() == 0

    try:
        profile = user.userprofile_set.all().get()
    except ObjectDoesNotExist:
        profile = None
    return render(request, 'challenge/user_display.html',
        {
            'profile_user': user,
            'profile': profile,
            'entries': entries,
            'given_awards': given_awards,
            'received_awards': received_awards,
            'possible_spammer': possible_spammer,
        }
    )


class ProfileForm(forms.ModelForm):
    twitter_username = forms.RegexField(
        regex=r'^@?\w{1,15}$',
        required=False,
        label="Twitter username",
        help_text=(
            "Add your Twitter username to show a link to your "
            "Twitter timeline on your profile."
        ),
        widget=forms.TextInput(attrs={
            'size': '20',
        })
    )
    github_username = forms.RegexField(
        regex=r'^[A-Za-z\d](?:[A-Za-z\d]|-(?=[A-Za-z\d])){0,38}$',
        required=False,
        label="GitHub username",
        help_text=(
            "Add your GitHub username to show a link to your "
            "GitHub account on your profile."
        ),
        widget=forms.TextInput(attrs={
            'size': '40',
        })
    )
    content = SafeHTMLField(
        label='Text to appear on your profile page',
        required=False,
        help_text='Basic HTML tags allowed: %s' % (', '.join(safeTags))
    )

    def clean_twitter_username(self):
        """Remove the @ from a Twitter username, if given."""
        v = self.cleaned_data.get('twitter_username')
        if not v:
            return None
        return v.strip('@')

    def clean_github_username(self):
        """Convert empty input to None."""
        return self.cleaned_data.get('github_username') or None

    class Meta:
        model = models.UserProfile
        fields = ['twitter_username', 'github_username', 'content']


def profile_description(request):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')

    try:
        profile = request.user.userprofile_set.get()
    except models.UserProfile.DoesNotExist:
        profile = models.UserProfile(user=request.user)

    if request.POST:
        form = ProfileForm(request.POST, instance=profile)
        if form.is_valid():
            form.instance.save()
            messages.success(request, 'Description saved!')
            return HttpResponseRedirect(f'/u/{request.user.username}/')
    else:
        form = ProfileForm(instance=profile)
    return render(
        request,
        'challenge/profile_description.html',
        {'form': form}
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
    for diary_entry, comments in list(d.items()):
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

    messages.success(request, f'Spammer deleted! ({user})')
    return HttpResponseRedirect('/u/%s/' % user_id)
