from django.urls import re_path

from .views import (
    ComposeEmail, EditEmail, DraftEmailList, PreviewEmail, PreviewEmailText,
    send, unsubscribe
)


urlpatterns = [
    re_path(r"^$", DraftEmailList.as_view(), name="draft-emails"),
    re_path(r"^unsubscribe$", unsubscribe, name="unsubscribe"),
    re_path(r"^compose$", ComposeEmail.as_view(), name="compose-email"),
    re_path(r"^(?P<pk>\d+)/$", PreviewEmail.as_view(), name="preview-email"),
    re_path(r"^(?P<pk>\d+)/text$", PreviewEmailText.as_view(), name="preview-email-text"),
    re_path(r"^(?P<pk>\d+)/edit$", EditEmail.as_view(), name="edit-email"),
    re_path(r"^(?P<pk>\d+)/send$", send, name="send-email"),
]
