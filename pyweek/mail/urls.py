from django.conf.urls import url

from .views import (
    ComposeEmail, EditEmail, DraftEmailList, PreviewEmail, PreviewEmailText,
    send, unsubscribe
)


urlpatterns = [
    url('^$', DraftEmailList.as_view(), name='draft-emails'),
    url('^unsubscribe$', unsubscribe, name='unsubscribe'),
    url('^compose$', ComposeEmail.as_view(), name='compose-email'),
    url(r'^(?P<pk>\d+)/$', PreviewEmail.as_view(), name='preview-email'),
    url(r'^(?P<pk>\d+)/text$', PreviewEmailText.as_view(), name='preview-email-text'),
    url(r'^(?P<pk>\d+)/edit$', EditEmail.as_view(), name='edit-email'),
    url(r'^(?P<pk>\d+)/send$', send, name='send-email'),
]
