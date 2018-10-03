from django.conf.urls import url

from .views import (
    ComposeEmail, EditEmail, DraftEmailList, PreviewEmail, PreviewEmailText,
    send
)


urlpatterns = [
    url('^$', DraftEmailList.as_view(), name='draft-emails'),
    url('^compose$', ComposeEmail.as_view(), name='compose-email'),
    url('^(?P<pk>\d+)/$', PreviewEmail.as_view(), name='preview-email'),
    url('^(?P<pk>\d+)/text$', PreviewEmailText.as_view(), name='preview-email-text'),
    url('^(?P<pk>\d+)/edit$', EditEmail.as_view(), name='edit-email'),
    url('^(?P<pk>\d+)/send$', send, name='send-email'),
]
