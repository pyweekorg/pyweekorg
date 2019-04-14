from django.conf.urls import url, include
from pyweek.challenge.views.message import DiaryFeed
from .views import (
    challenge, message, user, entry, files, poll, registration, award, pages,
    api
)

urlpatterns = [
    url(r'^$', challenge.index),
    url(r'^stats/$', challenge.stats),
    url(r'^stats.json$', challenge.stats_json),
    #url(r'^test/$', 'test'),
    #url(r'^update_has_final/$', 'update_has_final'),
    url(r'^all_games/$', challenge.all_games),
    url(r'^challenges/$', challenge.previous_challenges),

    url(r'^(\d+)/$', challenge.challenge_display, name="challenge"),
    url(r'^(\d+)/diaries/$', challenge.challenge_diaries),
    url(r'^(\d+)/ratings/$', challenge.challenge_ratings),

    url(r'^(\d+)/downloads\.json$', api.challenge_downloads),

    # Message views
    url(r'^messages/$', message.list_messages),
    url(r'^message_add/$', message.message_add),
    url(r'^d/(\d+)/$', message.diary_display, name="display-diary"),
    url(r'^d/(\d+)/edit/$', message.diary_edit),
    url(r'^d/(\d+)/delete/$', message.diary_delete),
    url(r'^e/([\w-]+)/diary/$', message.entry_diary),
    url(r'^d/feed/$', DiaryFeed(), name='diary_feed'),
    url(r'^update_messages/$', message.update_messages),

    # User views
    url(r'^u/([\w\. \-\[\]!]+)/$', user.user_display, name='user_display'),
    url(r'^u/([\w\. \-\[\]!]+)/delete_spam$', user.delete_spammer, name='delete_spammer'),
    url(r'^profile_description/$', user.profile_description),

    # Entry views
    url(r'^(\d+)/entry_add/$', entry.entry_add),
    url(r'^(\d+)/entries/$', entry.entry_list),
    url(r'^(\d+)/rating-dashboard$', entry.rating_dashboard),
    url(r'^e/([\w-]+)/$', entry.entry_display),
    url(r'^e/([\w-]+)/manage/$', entry.entry_manage),
    url(r'^e/([\w-]+)/ratings/$', entry.entry_ratings),

    # Files views
    url(r'^e/([\w-]+)/upload/$', files.entry_upload),
    url(r'^e/([\w-]+)/oup/$', files.oneshot_upload),
    url(r'^e/([\w-]+)/delete/(.+)$', files.file_delete),

    # Poll views
    url(r'^p/(\d+)/$', poll.poll_display),
    url(r'^p/(\d+)/view/$', poll.poll_view),
    url(r'^p/(\d+)/test/$', poll.poll_view),

    # Registration views
    url(r'^login/', registration.login_page ),
    url(r'^recover$', registration.recovery),
    url(r'^logout/', registration.logout ),
    url(r'^profile/$', registration.profile ),
    url(r'^profile/verify$', registration.verify_email),
    url(r'^register/', registration.register ),
    url(r'^resetpw/', registration.resetpw ),

    # Award views
    url(r'^e/([\w-]+)/upload_award/$', award.upload_award),
    url(r'^e/([\w-]+)/give_award/$', award.give_award),
    url(r'^a/(\d+)/$', award.view_award),
    url(r'^all_awards/$', award.view_all_awards),

    # Pages views
    url(r'^s/(\w+)/$', pages.page),
]
