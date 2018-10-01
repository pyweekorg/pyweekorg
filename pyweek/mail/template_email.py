from __future__ import unicode_literals
import pkgutil

import django.core.mail
from django.conf import settings
from django.template import Template, Context


class InvalidTemplate(Exception):
    """The selected template does not exist."""


def send_email(template_name, recipients, params):
    """Send a templated e-mail."""
    tmpl_bytes = pkgutil.get_data(
        __name__,
        'templates/emails/{}.txt'.format(template_name)
    )
    subject_source, body_source = tmpl_bytes.decode('utf-8').split('\n', 1)

    context = Context(params, autoescape=False)

    subject_template = Template(subject_source)
    subject = subject_template.render(context)

    body_template = Template(body_source.strip())
    body = body_template.render(context)

    django.core.mail.send_mail(
        subject=subject.strip(),
        message=body,
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=list(recipients),
        fail_silently=False,
    )
