import os
import sys
from django.db import models
from django.conf import settings
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
import django.contrib.auth

PY3 = sys.version_info >= (3,)


def default_verification_key():
    key = os.urandom(16)
    if PY3:
        key = key.hex()
    else:
        key = key.encode('hex')
    return key


class EmailAddress(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
    )

    address = models.EmailField()
    verified = models.BooleanField(editable=False, default=False)
    verification_key = models.CharField(
        max_length=32,
        unique=True,
        editable=False,
        default=default_verification_key,
    )

    def __repr__(self):
        return '<EmailAddress {!r} {}>'.format(
            self.address,
            'verified' if self.verified else 'UNVERIFIED'
        )

    def is_primary(self):
        """Return True if this is the primary e-mail address for the user."""
        return self.address == self.user.email

    def request_verification(self):
        """Send an e-mail address verification code."""

        from pyweek.mail import sending
        if self.verified:
            return
        self.verification_key = default_verification_key()
        self.save()
        sending.send_template(
            subject='E-mail verification',
            template_name='email-verification',
            recipients=[self.address],
            params={
                'user': self.user,
                'address': self.address,
                'verification_key': self.verification_key,
            },
            priority=sending.PRIORITY_IMMEDIATE,
            reason='because someone, possibly you, entered ' +
                   'your e-mail address at pyweek.org.',
        )


class UserSettings(models.Model):
    """A user's personal settings."""

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='settings',
    )

    email_contest_updates = models.BooleanField(
        help_text="Can we e-mail you about contests you are registered in?",
        default=True,
    )
    email_replies = models.BooleanField(
        help_text="Do you want to receive replies to your diary posts and " +
                  "comments by e-mail?",
        default=True,
    )
    email_news = models.BooleanField(
        help_text="Can we e-mail you (rarely) about Pyweek news, such as " +
                  "upcoming competitions?",
        default=True
    )


@receiver(post_save, sender=django.contrib.auth.get_user_model())
def create_profile(sender, instance, created, **kwargs):
    if not created:
        # Don't do anything if saving an existing object
        return

    UserSettings.objects.get_or_create(user=instance)
    if instance.email:
        obj, address_created = EmailAddress.objects.get_or_create(
            user=instance,
            address=instance.email,
        )
        if address_created:
            obj.request_verification()
