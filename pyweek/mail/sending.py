import pkgutil
import re
import string
from typing import AnyStr, Iterable, Any

import django.core.mail
from django.conf import settings
from django.template.loader import render_to_string
from django.core import signing

import mailer
import html2text

from pyweek.users.models import EmailAddress


# Extend the django-mailer priorities with PRIORITY_IMMEDIATE
# that allows skipping the queue. This is mostly important
# for e-mail validation, which is effectively an interactive
# process.
PRIORITY_LOW = mailer.get_priority('low')
PRIORITY_MEDIUM = mailer.get_priority('medium')
PRIORITY_HIGH = mailer.get_priority('high')
PRIORITY_IMMEDIATE = -1


REASON_COMMENTS = (
    "because you are set to receive replies to diary and discussion posts."
)

UNSUBSCRIBE_SIGNER = signing.Signer(salt='unsubscribe')


def rotate(s: str) -> str:
    """Rot13 the given alphabet."""
    assert len(s) == 26
    return s[13:] + s[:13]


ROT13_TABLE = str.maketrans(
    string.ascii_lowercase + string.ascii_uppercase,
    rotate(string.ascii_lowercase) + rotate(string.ascii_uppercase)
)


def rot13(s: str) -> str:
    """rot13 a string in order to obfuscate it.

    This is not a crucial security measure because we use cryptographic
    signing; really the only reason to do it is to discourage probing
    of the system.
    """
    return s.translate(ROT13_TABLE)



class InvalidTemplate(Exception):
    """The selected template does not exist."""


def _make_payload(body_html: str, reason: str) -> tuple[str, str]:
    converter = html2text.HTML2Text()
    converter.inline_links = False
    body_text = converter.handle(body_html).strip()
    ctx = {
        'body_html': body_html,
        'body_text': body_text,
        'reason': reason,
    }
    html_part = render_to_string('mail/admin_email.html', context=ctx)
    text_part = render_to_string('mail/admin_email.txt', context=ctx)
    return html_part, text_part


WS_RE = re.compile(r'[\r\n]+')
TOKEN_KEY = '%%UNSUBSCRIBE_TOKEN%%'


def clean_header(v: str) -> str:
    """Clean a header value, removing illegal characters."""
    return WS_RE.sub(' ', v)


def send(
    subject: str,
    html_body: str,
    recipients: Iterable[str],
    reason: str,
    priority: int = PRIORITY_MEDIUM
) -> None:
    """Send an e-mail, using the django-mailer queue."""
    html_part, text_part = _make_payload(html_body, reason)
    subject = f'[PyWeek] {subject.strip()}'

    #TODO: identify sending user rather than using default
    from_email = settings.DEFAULT_FROM_EMAIL
    for recip in recipients:
        if isinstance(recip, EmailAddress):
            to_email = f'"{recip.user.username}" <{recip.address}>'
            token_key = recip.user.username
        else:
            token_key = to_email = recip

        token = UNSUBSCRIBE_SIGNER.sign(rot13(token_key))

        to_email = clean_header(to_email)
        subject = clean_header(subject.strip())

        # FIXME: substituting a token into the generated output is not
        # infallible, but this might be a lot faster than re-rendering a
        # template for each user, which matters when sending to 1000+ users.
        user_html = html_part.replace(TOKEN_KEY, token)
        user_text = text_part.replace(TOKEN_KEY, token)

        if priority == PRIORITY_IMMEDIATE:
            django.core.mail.send_mail(
                subject=subject,
                message=user_text,
                html_message=user_html,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[to_email],
                fail_silently=False,
            )
        else:
            mailer.send_html_mail(
                subject=subject,
                message=user_text,
                message_html=user_html,
                from_email=from_email,
                recipient_list=[to_email],
                priority=priority,
            )


def send_template(
    subject: str,
    template_name: str,
    recipients: Iterable[str],
    params: dict[str, Any],
    reason: str,
    priority: int = PRIORITY_MEDIUM
) -> None:
    """Send a queued message from a template."""
    html_body = render_to_string(
        f'emails/{template_name}.html',
        context=params
    )
    send(
        subject,
        html_body,
        recipients,
        reason,
        priority=priority
    )
