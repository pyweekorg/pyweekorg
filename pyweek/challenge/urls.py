from django.urls import re_path
from pyweek.challenge.views.message import DiaryFeed
from .views import (
    challenge, message, user, entry, files, poll, registration, award, pages,
    api
)

urlpatterns = [
    re_path(r"^$", challenge.index),
    re_path(r"^stats/$", challenge.stats),
    re_path(r"^stats.json$", challenge.stats_json),
    #url(r'^test/$', 'test'),
    #url(r'^update_has_final/$', 'update_has_final'),
    re_path(r"^all_games/$", challenge.all_games),
    re_path(r"^challenges/$", challenge.previous_challenges),

    re_path(r"^(\d+)/$", challenge.challenge_display, name="challenge"),
    re_path(r"^(\d+)/diaries/$", challenge.challenge_diaries),
    re_path(r"^(\d+)/ratings/$", challenge.challenge_ratings),

    re_path(r"^(\d+)/downloads\.json$", api.challenge_downloads),

    # Message views
    re_path(r"^messages/$", message.list_messages),
    re_path(r"^message_add/$", message.message_add),
    re_path(r"^d/(\d+)/$", message.diary_display, name="display-diary"),
    re_path(r"^d/(\d+)/edit/$", message.diary_edit),
    re_path(r"^d/(\d+)/delete/$", message.diary_delete),
    re_path(r"^e/([\w-]+)/diary/$", message.entry_diary),
    re_path(r"^d/feed/$", DiaryFeed(), name="diary_feed"),
    re_path(r"^update_messages/$", message.update_messages),

    # User views
    re_path(r"^u/([\w\. \-\[\]!]+)/$", user.user_display, name="user_display"),
    re_path(r"^u/([\w\. \-\[\]!]+)/delete_spam$", user.delete_spammer, name="delete_spammer"),
    re_path(r"^profile_description/$", user.profile_description),

    # Entry views
    re_path(r"^(\d+)/entry_add/$", entry.entry_add),
    re_path(r"^(\d+)/entries/$", entry.entry_list),
    re_path(r"^(\d+)/rating-dashboard$", entry.rating_dashboard),
    re_path(r"^e/([\w-]+)/$", entry.entry_display),
    re_path(r"^e/([\w-]+)/manage/$", entry.entry_manage),
    re_path(r"^e/([\w-]+)/members/$", entry.entry_requests),
    re_path(r"^e/([\w-]+)/ratings/$", entry.entry_ratings),

    # Files views
    re_path(r"^e/([\w-]+)/upload/$", files.entry_upload),
    re_path(r"^e/([\w-]+)/oup/$", files.oneshot_upload),
    re_path(r"^e/([\w-]+)/delete/(.+)$", files.file_delete),

    # Poll views
    re_path(r"^p/(\d+)/$", poll.poll_display),
    re_path(r"^p/(\d+)/view/$", poll.poll_view),
    re_path(r"^p/(\d+)/test/$", poll.poll_view),

    # Registration views
    re_path(r"^login/", registration.login_page),
    re_path(r"^recover$", registration.recovery),
    re_path(r"^logout/", registration.logout),
    re_path(r"^profile/$", registration.profile),
    re_path(r"^profile/verify$", registration.verify_email),
    re_path(r"^register/", registration.register),
    re_path(r"^resetpw/", registration.resetpw),

    # Award views
    re_path(r"^e/([\w-]+)/upload_award/$", award.upload_award),
    re_path(r"^e/([\w-]+)/give_award/$", award.give_award),
    re_path(r"^a/(\d+)/$", award.view_award),
    re_path(r"^all_awards/$", award.view_all_awards),

    # Pages views
    re_path(r"^s/(\w+)/$", pages.page),
]
