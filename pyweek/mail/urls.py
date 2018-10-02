from django.conf.urls import url

from .views import ComposeEmail, EditEmail, DraftEmailList, PreviewEmail


urlpatterns = [
    url('^$', DraftEmailList.as_view(), name='draft-emails'),
    url('^compose$', ComposeEmail.as_view(), name='compose-email'),
    url('^(?P<pk>\d+)/$', PreviewEmail.as_view(), name='preview-email'),
    url('^(?P<pk>\d+)/edit$', EditEmail.as_view(), name='edit-email'),
]
