import django.core.mail
from .models import EmailTemplate

from django.template import Template, Context


class InvalidTemplate(Exception):
    """The selected template does not exist."""


def send_email(template_name, recipients, params):
    """Send a templated e-mail."""
    try:
        template = EmailTemplate.objects.get(name=template_name)
    except EmailTemplate.DoesNotExist:
        raise InvalidTemplate(
            "No template defined named {!r}".format(template_name)
        )

    context = Context(params, autoescape=False)

    subject_template = Template(template.subject)
    subject = subject_template.render(context)

    body_template = Template(template.body)
    body = body_template.render(context)

    django.core.mail.send_mail(
        subject.strip(),
        body,
        list(recipients),
        fail_silently=False,
    )
