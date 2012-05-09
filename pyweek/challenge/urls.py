from django.conf.urls.defaults import *
#from django.conf.settings import DEBUG

urlpatterns = patterns('pyweek.challenge.views.challenge',
    (r'^/?$', 'index'),
    (r'^stats/$', 'stats'),
    (r'^stats.json$', 'stats_json'),
    #(r'^test/$', 'test'),
    #(r'^update_messages/$', 'update_messages'),
    #(r'^update_has_final/$', 'update_has_final'),
    (r'^all_games/$', 'all_games'),

    (r'^(\d+)/$', 'challenge_display'),
    (r'^(\d+)/ratings/$', 'challenge_ratings'),
    (r'^(\d+)/calculate_rating_tallies/', 'calculate_rating_tallies'),
    (r'^(\d+)/fix_winners/', 'fix_winners'),
)

urlpatterns += patterns('pyweek.challenge.views.message',
    (r'^messages/$', 'list_messages'),
    (r'^message_add/$', 'message_add'),
    (r'^d/(\d+)/$', 'diary_display'),
    (r'^d/(\d+)/edit/$', 'diary_edit'),
    (r'^d/(\d+)/delete/$', 'diary_delete'),
    (r'^e/([\w-]+)/diary/$', 'entry_diary'),
)

urlpatterns += patterns('pyweek.challenge.views.user',
    (r'^u/([\w\. \-[\]]+)/$', 'user_display'),
    (r'^profile_description/$', 'profile_description'),
)

urlpatterns += patterns('pyweek.challenge.views.entry',
    (r'^(\d+)/entry_add/$', 'entry_add'),
    (r'^(\d+)/entries/$', 'entry_list'),
    (r'^e/([\w-]+)/$', 'entry_display'),
    (r'^e/([\w-]+)/manage/$', 'entry_manage'),
    (r'^e/([\w-]+)/ratings/$', 'entry_ratings'),
)

urlpatterns += patterns('pyweek.challenge.views.files',
    (r'^e/([\w-]+)/upload/$', 'entry_upload'),
    (r'^e/([\w-]+)/oup/$', 'oneshot_upload'),
    (r'^e/([\w-]+)/delete/(.+)$', 'file_delete'),
)

urlpatterns += patterns('pyweek.challenge.views.poll',
    (r'^p/(\d+)/$', 'poll_display'),
    (r'^p/(\d+)/view/$', 'poll_view'),
    (r'^p/(\d+)/test/$', 'poll_view'),
)

urlpatterns += patterns('pyweek.challenge.views.registration',
    (r'^login/', 'login_page' ),
    (r'^logout/', 'logout' ),
    (r'^profile/', 'profile' ),
    (r'^register/', 'register' ),
    (r'^resetpw/', 'resetpw' ),
)

urlpatterns += patterns('pyweek.challenge.views.award',
    (r'^e/([\w-]+)/upload_award/$', 'upload_award'),
    (r'^e/([\w-]+)/give_award/$', 'give_award'),
    (r'^a/(\d+)/$', 'view_award'),
    (r'^all_awards/$', 'view_all_awards'),
)

urlpatterns += patterns('pyweek.challenge.views.pages',
    (r'^s/(\w+)/$', 'page'),
)

urlpatterns += patterns('django.views.static',
    (r'^js/(?P<path>.*)$', 'serve',
        {'document_root': '/home/pyweek/lib/pyweek/challenge/media/js'}),
    (r'(^favicon\.ico$)', 'serve',
        {'document_root': '/home/pyweek/lib/pyweek/challenge/media/'}),
)

