import os, cgi
import datetime
import xml.sax.saxutils

from django import newforms
from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse, HttpResponseRedirect
from pyweek.challenge import models
from pyweek import settings

from stripogram import html2text, html2safehtml

safeTags = '''strong em blockquote pre b a i br img table tr th td pre p dl dd dt ul ol li span div'''.split()

class SafeHTMLField(newforms.CharField):
    widget = newforms.Textarea
    def clean(self, value):
        if '<' in value:
            value = html2safehtml(value, safeTags)
        if not value: raise newforms.ValidationError(['This field is required'])
        return value


MESSAGES_PER_PAGE = 30

def update_messages(request):
    for entry in models.DiaryEntry.objects.filter(is_pyggy=False):
        #try:
            #comment = entry.diarycomment_set.latest()
        #except models.DiaryComment.DoesNotExist:
            #continue
        #entry.actor = comment.user
        #entry.last_comment = comment
        #entry.activity = comment.created
        entry.reply_count = entry.diarycomment_set.count()
        entry.save()
    request.user.message_set.create(message='messages updated')
    return render_to_response('challenge/index.html',
        {} , context_instance=RequestContext(request))

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
            author = comm and diary.actor or diary.user,
            date = date,
            commid = comm and comm.id,
        )
        diary_entries.append(d)
    return diary_entries

def messages(request):
    try:
        start = int(request.GET.get('start', 0))
    except:
        # XXX haxx0rs trying to inject SQL into my codez
        start = 0

    # entries to display
    entries = models.DiaryEntry.objects.filter(is_pyggy=False,
        sticky=False).order_by('-activity')
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

    sticky_entries = models.DiaryEntry.objects.filter(is_pyggy=False,
        sticky=True).order_by('-activity')
    sticky_entries = extract_entries(sticky_entries)

    return render_to_response('messages.html', {
        'sticky_entries': sticky_entries,
        'diary_entries': diary_entries,
        'pages': pages,
        'prev': start and start-MESSAGES_PER_PAGE or None,
        'last': (m-1) * MESSAGES_PER_PAGE,
        'more_start': more_start,
        'more_end': more_end,
        'next': start+MESSAGES_PER_PAGE < num and start+MESSAGES_PER_PAGE or None,
    } , context_instance=RequestContext(request))


class DiaryForm(newforms.Form):
    title = newforms.CharField(required=True, widget=newforms.TextInput(attrs={'size':'60'}))
    content = SafeHTMLField(required=True)
        #help_text='Basic HTML tags allowed: %s'%(', '.join(safeTags)))
    def as_plain(self):
        return self._html_output(u'<b>%(label)s</b><br>%(field)s<br>%(help_text)s<br>%(errors)s',
             u'%s', '', u' %s', False)

def message_add(request):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    previewed = False
    content = title = ''
    if request.POST:
        form = DiaryForm(request.POST)
        if form.is_valid():
            content = form.clean_data['content']

            previewed = True
            if 1: #request.POST.has_key('save'):
                # do the save
                diary = models.DiaryEntry()
                diary.content = content
                diary.user = request.user
                diary.actor = request.user
                diary.title = form.clean_data['title']
                diary.created = datetime.datetime.now(models.UTC)
                diary.save()
                generate_diary_rss()
                request.user.message_set.create(message='Entry saved!')
                return HttpResponseRedirect('/d/%s/'%diary.id)
    else:
        form = DiaryForm()

    return render_to_response('message_add.html',
        {
            'previewed': previewed,
            'content': content,
            'title': title,
            'form': form,
        }, context_instance=RequestContext(request))

def entry_diary(request, entry_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)
    is_member = request.user in entry.users.all()
    if not is_member:
        request.user.message_set.create(message="You're not allowed to add diary entries!")
        return HttpResponseRedirect('/e/%s/'%entry_id)
    challenge = entry.challenge

    previewed = False
    content = title = ''
    if request.POST:
        form = DiaryForm(request.POST)
        if form.is_valid():
            content = form.clean_data['content']

            previewed = True
            if 1: #request.POST.has_key('save'):
                # do the save
                diary = models.DiaryEntry()
                diary.entry = entry
                diary.challenge = challenge
                diary.content = content
                diary.user = request.user
                diary.actor = request.user
                diary.title = form.clean_data['title']
                diary.created = datetime.datetime.now(models.UTC)
                diary.save()
                generate_diary_rss()
                request.user.message_set.create(message='Entry saved!')
                return HttpResponseRedirect('/d/%s/'%diary.id)
    else:
        form = DiaryForm()

    return render_to_response('challenge/add_diary.html',
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
        }, context_instance=RequestContext(request))

feed_template = u'''<?xml version="1.0" encoding="UTF-8" standalone="no"?>
<rss version="2.0">
 <channel>
  <title>PyWeek Diary Entries</title>
  <link>http://pyweek.org/</link>
  <description>The latest 40 entries from diaries at the
  PyWeek challenge</description>
  <managingEditor>richard@pyweek.org (Richard Jones)</managingEditor>
  <language>en</language>
  %(items)s
 </channel>
</rss>
'''

item_template = u'''
  <item>
   <title>%(title)s</title>
   <pubDate>%(date)s</pubDate>
   <link>%(url)s</link>
   <guid>%(url)s</guid>
   <description>%(content)s&lt;br&gt;-- %(author)s</description>
  </item>
'''

def unicode_god_damnit(s):
    if isinstance(s, str):
        try:
            s = s.decode('utf8')
        except UnicodeDecodeError:
            s = s.decode('ascii', 'replace')
    return s

def generate_diary_rss():
    l = []
    e = xml.sax.saxutils.escape
    for diary in models.DiaryEntry.objects.\
            filter(is_pyggy=False).order_by('-created')[:40]:
        entry = diary.entry
        title = cgi.escape(unicode_god_damnit(diary.title))
        if entry:
            s = unicode_god_damnit(entry.title)
            author = cgi.escape('%s of <a href="http://pyweek.org/e/%s/">%s</a>'%(
                diary.user, entry.name, e(s)))
        else:
            author = cgi.escape(str(diary.user))
        url = 'http://pyweek.org/d/%s/'%diary.id
        date = diary.created.strftime("%a, %d %b %Y %H:%M:%S -0600")
        content = cgi.escape(unicode_god_damnit(diary.content))
        l.append(item_template%locals())
    items = '\n'.join(l)
    f = open(settings.DIARY_RSS_FILE_NEW, 'w')
    f.write((feed_template%locals()).encode('utf8'))
    f.close()
    os.rename(settings.DIARY_RSS_FILE_NEW, settings.DIARY_RSS_FILE)

class CommentForm(newforms.Form):
    content = SafeHTMLField(required=True)
        #help_text='Basic HTML tags allowed: %s'%(', '.join(safeTags)))
    def as_plain(self):
        return self._html_output(u'%(field)s<br>%(help_text)s<br>%(errors)s',
             u'%s', '', u' %s', False)

def diary_display(request, diary_id):
    diary = get_object_or_404(models.DiaryEntry, pk=diary_id)
    entry = diary.entry
    challenge = diary.challenge
    is_member = entry and request.user in entry.users.all()

    previewed = False
    content = ''
    if request.POST:
        previewed = True
        form = CommentForm(request.POST)
        if form.is_valid():
            content = form.clean_data['content']

            if 1: # request.POST.has_key('save'):
                # do the save
                comment = models.DiaryComment(content=content,
                    challenge=challenge, user=request.user, diary_entry=diary)
                comment.save()
                diary.activity = datetime.datetime.now(models.UTC)
                diary.actor = request.user
                diary.last_comment = comment
                diary.reply_count = diary.reply_count + 1
                diary.save()
                request.user.message_set.create(message='Comment added!')
                return HttpResponseRedirect('/d/%s/#%s'%(diary_id,
                    comment.id))
    else:
        form = CommentForm()
        content = diary.content

    return render_to_response('challenge/diary.html',
        {
            'challenge': challenge,
            'entry': entry,
            'diary': diary,
            'is_user': not request.user.is_anonymous(),
            'previewed': previewed,
            'content': content,
            'form': form,
            'comments': diary.diarycomment_set.all(),
            'is_member': is_member,
            'is_owner': entry and entry.user == request.user,
        }, context_instance=RequestContext(request))


def diary_edit(request, diary_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/?next=/d/%s/edit/'%diary_id)
    diary = get_object_or_404(models.DiaryEntry, pk=diary_id)
    if request.user != diary.user:
        request.user.message_set.create(message="You can't edit this entry!")
        return HttpResponseRedirect('/d/%s/'%diary_id)

    data = {'content': diary.content, 'title': diary.title}

    if request.POST:
        form = DiaryForm(request.POST)
        if form.is_valid():
            content = form.clean_data['content']

            # do the save
            diary.content = content
            diary.title = form.clean_data['title']
            diary.edited = datetime.datetime.now(models.UTC)
            diary.save()
            request.user.message_set.create(message='Edit saved!')
            return HttpResponseRedirect('/d/%s/edit/'%diary_id)
    else:
        form = DiaryForm(data)
    return render_to_response('challenge/diary_edit.html',
        {
            'diary': diary,
            'challenge': diary.challenge,
            'entry': diary.entry,
            'form': form,
        }, context_instance=RequestContext(request))


def diary_delete(request, diary_id):
    if request.user.is_anonymous():
        return HttpResponseRedirect('/login/')
    diary = get_object_or_404(models.DiaryEntry, pk=diary_id)
    if request.user != diary.user:
        request.user.message_set.create(message="You can't delete this entry!")
        return HttpResponseRedirect('/d/%s/'%diary_id)

    if request.POST and 'delete' in request.POST:
        diary.delete()
        generate_diary_rss()
        request.user.message_set.create(message="Diary entry deleted!")
        return HttpResponseRedirect('/e/%s/'%diary.entry_id)
    else:
        return HttpResponseRedirect('/d/%s/'%diary_id)

