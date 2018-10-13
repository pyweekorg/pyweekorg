import os, cgi
import datetime
import xml.sax.saxutils

from django import forms
from django.db.models import Q
from django.contrib import messages
from django.contrib.syndication.views import Feed
from django.shortcuts import get_object_or_404, render
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect

from pyweek.challenge import models
from pyweek import settings
from pyweek.users.models import EmailAddress
from pyweek.mail import sending
from pyweek.activity.models import log_event
from pyweek.activity.summary import summarise

from stripogram import html2text, html2safehtml

safeTags = '''strong em blockquote pre b a i br img table tr th td pre p dl dd dt ul ol li span div'''.split()

class SafeHTMLField(forms.CharField):
    widget = forms.Textarea
    def clean(self, value):
        if '<' in value:
            value = html2safehtml(value, safeTags)
        if not value: raise forms.ValidationError(['This field is required'])
        return value


MESSAGES_PER_PAGE = 30

def update_messages(request):
    for entry in models.DiaryEntry.objects.filter(is_pyggy=False):
        try:
            comment = entry.diarycomment_set.latest()
        except models.DiaryComment.DoesNotExist:
            entry.actor = entry.user
            entry.last_comment = None
            entry.activity = entry.created
            entry.reply_count = 0
        else:
            entry.actor = comment.user
            entry.last_comment = comment
            entry.activity = comment.created
            entry.reply_count = entry.diarycomment_set.count()
        entry.save()
    messages.success(request, 'Messages updated')
    return render(request, 'challenge/index.html', {})


def extract_entries(entries):
    diary_entries = []
    now = datetime.datetime.utcnow()
    for diary in entries:
        entry = diary.entry
        comm = diary.last_comment

        activity = diary.activity
        delta = now - activity
        if activity.year != now.year:
            date = activity.strftime('%d %%b %%Y'%activity.day)
        elif delta.days < 1:
            if delta.seconds < 30:
                date = 'just now'
            elif delta.seconds < 120:
                date = 'a minute ago'
            elif delta.seconds < 7200:
                date = '%d minutes ago'%(delta.seconds/60)
            else:
                date = '%d hours ago'%(delta.seconds/3600)
        elif delta.days == 1:
            date = activity.strftime('%H:%M yesterday')
        elif delta.days < 8:
            date = activity.strftime('%H:%M %A')
        else:
            date = activity.strftime('%%a %d %%b'%activity.day)
        d = dict(
            title = diary.title,
            id = diary.id,
            entry = entry and entry.title,
            entry_name = entry and entry.name,
            reply_count = diary.reply_count,
            originator=diary.user,
            sticky=diary.sticky,
            author = comm and diary.actor or diary.user,
            date = date,
            commid = comm and comm.id,
        )
        diary_entries.append(d)
    return diary_entries


def list_messages(request):
    try:
        start = int(request.GET.get('start', 0))
    except:
        # XXX haxx0rs trying to inject SQL into my codez
        start = 0

    # entries to display
    entries = models.DiaryEntry.objects.filter(
        is_pyggy=False,
        entry__isnull=True).order_by('-sticky', '-activity')
    diary_entries = extract_entries(entries[start:start + MESSAGES_PER_PAGE])

    # pagination
    n = start / MESSAGES_PER_PAGE
    num = len(entries)
    m = (num / MESSAGES_PER_PAGE) + 1
    if n < 5:
        s = 0
        e = n + 10
        more_start = False
        more_end = True
    elif n + 5 > m:
        s = n - 5
        e = m
        more_start = True
        more_end = False
    else:
        s = n - 5
        e = n + 5
        more_start = True
        more_end = True

    pages = [
        dict(num=i+1, start=i*MESSAGES_PER_PAGE,
            current=start==i*MESSAGES_PER_PAGE)
                for i in range(s, e)
    ]

    return render(request, 'messages.html', {
        'diary_entries': diary_entries,
        'pages': pages,
        'prev': start and start-MESSAGES_PER_PAGE or None,
        'last': (m-1) * MESSAGES_PER_PAGE,
        'more_start': more_start,
        'more_end': more_end,
        'next': start+MESSAGES_PER_PAGE < num and start+MESSAGES_PER_PAGE or None,
    })


class DiaryForm(forms.Form):
    title = forms.CharField(required=True, widget=forms.TextInput(attrs={'size':'60'}))
    content = SafeHTMLField(required=True,
        help_text='Basic HTML tags allowed: %s'%(', '.join(safeTags)))
    def as_plain(self):
        return self._html_output(u'<b>%(label)s</b><br>%(field)s<br>%(help_text)s<br>%(errors)s',
             u'%s', '', u' %s', False)


class StickyDiaryForm(DiaryForm):
    sticky = forms.BooleanField(required=False)


def message_add(request):
    is_anon = request.user.is_anonymous()
    if is_anon:
        return HttpResponseRedirect('/login/')
    is_super = not is_anon and request.user.is_superuser
    previewed = False
    content = title = ''

    if is_super:
        cls = StickyDiaryForm
    else:
        cls = DiaryForm

    if request.POST:
        form = cls(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']

            previewed = True
            # do the save
            diary = models.DiaryEntry()
            diary.content = content
            diary.user = request.user
            diary.actor = request.user
            diary.title = form.cleaned_data['title']
            if is_super:
                diary.sticky = form.cleaned_data.get('sticky', False)
            diary.created = datetime.datetime.utcnow()
            diary.save()

            desc, truncated = summarise(diary.content)
            log_event(
                type='new-thread',
                user=request.user,
                target=diary,
                title=diary.title,
                id=diary.id,
                description=desc,
                description_truncated=truncated,
            )
            messages.success(request, 'Entry saved!')
            return HttpResponseRedirect('/d/%s/'%diary.id)
    else:
        form = cls()

    return render(request, 'message_add.html',
        {
            'previewed': previewed,
            'content': content,
            'title': title,
            'form': cls,
        }
    )


def entry_diary(request, entry_id):
    is_anon = request.user.is_anonymous()
    if is_anon:
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    is_member = request.user in entry.users.all()
    if not is_member:
        messages.error(request, "You're not allowed to add diary entries!")
        return HttpResponseRedirect('/e/%s/'%entry_id)
    challenge = entry.challenge

    is_super = not is_anon and request.user.is_superuser

    previewed = False
    content = title = ''
    if is_super:
        cls = StickyDiaryForm
    else:
        cls = DiaryForm

    if request.POST:
        form = cls(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']

            previewed = True
            # do the save
            diary = models.DiaryEntry()
            diary.entry = entry
            diary.challenge = challenge
            diary.content = content
            diary.user = request.user
            diary.actor = request.user
            diary.title = form.cleaned_data['title']
            diary.created = datetime.datetime.utcnow()
            if is_super:
                diary.sticky = form.cleaned_data.get('sticky', False)
            diary.save()

            desc, truncated = summarise(diary.content)
            log_event(
                type='new-diary',
                user=request.user,
                target=diary,
                title=diary.title,
                entry={
                    'title': diary.entry.display_title,
                    'name': diary.entry.name,
                },
                description=desc,
                description_truncated=truncated,
            )
            messages.success(request, 'Entry saved!')
            return HttpResponseRedirect('/d/%s/'%diary.id)
    else:
        form = cls()

    return render(request, 'challenge/add_diary.html',
        {
            'previewed': previewed,
            'content': content,
            'title': title,
            'form': form,
            'challenge': challenge,
            'entry': entry,
            'diary_entries': entry.diaryentry_set.all(),
            'is_member': True,
            'is_owner': entry.user == request.user,
        }
    )


class DiaryFeed(Feed):
    title = "PyWeek Diary Entries"
    link = "/"
    description = "The latest 40 entries from diaries at the PyWeek challenge."

    def items(self):
        return models.DiaryEntry.objects.order_by('-created')[:40]

    def item_title(self, item):
        return item.title

    def item_author_name(self, item):
        return str(item.user)

    def item_description(self, item):
        return item.content

    def item_pubdate(self, item):
        return item.created

class CommentForm(forms.Form):
    content = SafeHTMLField(required=True,
        help_text='Basic HTML tags allowed: %s'%(', '.join(safeTags)))
    def as_plain(self):
        return self._html_output(u'%(field)s<br>%(help_text)s<br>%(errors)s',
             u'%s', '', u' %s', False)


def diary_display(request, diary_id):
    """Display a message thread."""
    diary = get_object_or_404(models.DiaryEntry, pk=diary_id)
    entry = diary.entry
    challenge = diary.challenge
    is_member = entry and request.user in entry.users.all()

    is_anon = request.user.is_anonymous()

    previewed = False
    if request.POST:
        form = CommentForm(request.POST)
        if form.is_valid():
            previewed = True

            # do the save
            comment = models.DiaryComment(content=form.cleaned_data['content'],
                challenge=challenge, user=request.user, diary_entry=diary)
            comment.save()
            diary.activity = datetime.datetime.utcnow()
            diary.actor = request.user
            diary.last_comment = comment
            diary.reply_count = diary.reply_count + 1
            diary.save()
            messages.success(request, 'Comment added!')

            # Send notifies
            addresses = EmailAddress.objects.filter(
                user__settings__email_replies=True,
            ).filter(
                # TODO: filter by users who want to receive notifications
                Q(user__diarycomment__diary_entry=diary) | Q(user=diary.user)
            ).exclude(user=request.user).distinct().select_related('user')
            sending.send_template(
                subject='New comment from {} on "{}"'.format(
                    request.user.username,
                    diary.title
                ),
                template_name='diary-reply',
                recipients=addresses,
                params={
                    'diary': diary,
                    'comment': comment,
                },
                reason=sending.REASON_COMMENTS
            )

            return HttpResponseRedirect('/d/%s/#%s'%(diary_id,
                comment.id))
    else:
        form = CommentForm()

    return render(request, 'challenge/diary.html', {
        'challenge': challenge,
        'entry': entry,
        'diary': diary,
        'is_user': not request.user.is_anonymous(),
        'previewed': previewed,
        'content': diary.content,
        'form': form,
        'comments': diary.diarycomment_set.all(),
        'is_member': is_member,
        'is_owner': entry and entry.user == request.user,
    })


def diary_edit(request, diary_id):
    is_anon = request.user.is_anonymous()
    if is_anon:
        return HttpResponseRedirect('/login/?next=/d/%s/edit/'%diary_id)
    diary = get_object_or_404(models.DiaryEntry, pk=diary_id)
    if request.user != diary.user:
        messages.error(request, "You can't edit this entry!")
        return HttpResponseRedirect('/d/%s/'%diary_id)

    is_super = not is_anon and request.user.is_superuser

    data = {'content': diary.content, 'title': diary.title}
    if is_super:
        data['sticky'] = diary.sticky

    if is_super:
        cls = StickyDiaryForm
    else:
        cls = DiaryForm

    if request.POST:
        form = cls(request.POST)
        if form.is_valid():
            content = form.cleaned_data['content']

            # do the save
            diary.content = content
            diary.title = form.cleaned_data['title']
            diary.edited = datetime.datetime.utcnow()
            if is_super:
                diary.sticky = form.cleaned_data.get('sticky', False)
            diary.save()
            messages.success(request, 'Edit saved!')
            return HttpResponseRedirect('/d/%s/edit/'%diary_id)
    else:
        form = cls(data)
    return render(request, 'challenge/diary_edit.html',
        {
            'diary': diary,
            'challenge': diary.challenge,
            'entry': diary.entry,
            'form': form,
            'is_super': is_super,
        }
    )


def diary_delete(request, diary_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    diary = get_object_or_404(models.DiaryEntry, pk=diary_id)
    if request.user != diary.user:
        messages.error(request, "You can't delete this entry!")
        return HttpResponseRedirect('/d/%s/'%diary_id)

    if request.POST and 'delete' in request.POST:
        diary.delete()
        messages.success(request, "Diary entry deleted!")
        return HttpResponseRedirect('/messages/')
    else:
        return HttpResponseRedirect('/d/%s/'%diary_id)

