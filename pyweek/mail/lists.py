"""Configuration for mailing lists - sets of users to e-mail.

All list providers should return an iterable of EmailAddress objects.

"""
from django.db.models import Q, F
from pyweek.challenge.models import Challenge
from pyweek.users.models import EmailAddress


LISTS = {}

def register(name):
    """Decorator to register the list provider."""
    def dec(f):
        return f
    return dec


def all_users():
    """A list of all users."""
    return filter_verified(EmailAddress.objects.filter(
        user__settings__email_news=True,
    ).distinct())


def latest_challenge_users(challenge=None):
    """E-mail participants in the latest challenge."""
    challenge = challenge or Challenge.objects.latest()
    return filter_verified(EmailAddress.objects.filter(
        user__entry__challenge=challenge,
        user__settings__email_contest_updates=True,
    ).distinct())


def filter_verified(addresses):
    """Given a QuerySet of addresses, return the ones we can e-mail.

    We currently e-mail verified e-mail addresses or unverified e-mail
    addresses that are set as the primary e-mail address. At a later date
    (when users have had a chance to verify their e-mail addresses) we can
    change this to only e-mail verified addresses.

    """
    return addresses.filter(
        Q(verified=True) | Q(address=F('user__email'))
    )
