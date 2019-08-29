"""Configuration for mailing lists - sets of users to e-mail.

All list providers should return an iterable of EmailAddress objects.

"""
from __future__ import unicode_literals
from collections import OrderedDict
from django.conf import settings
from django.db.models import Q, F, Count
from pyweek.challenge.models import Challenge
from pyweek.users.models import EmailAddress


LISTS = OrderedDict()


def address_list(name, reason):
    """Decorator to register the list provider."""
    assert reason.startswith('because ')
    assert reason.endswith('.')
    def dec(f):
        LISTS[f.__name__] = (name, f)
        f.name = name
        f.reason = reason
        return f
    return dec


@address_list(
    'All users',
    reason="because you are a registered user at pyweek.org."
)
def all_users():
    """A list of all users."""
    return filter_verified(EmailAddress.objects.filter(
        user__settings__email_news=True,
    ).distinct())


@address_list(
    'Verified addresses',
    reason="because you are a registered user at pyweek.org."
)
def verified_users(challenge=None):
    """Verified e-mail accounts."""
    return EmailAddress.objects.filter(
        user__settings__email_contest_updates=True,
        verified=True,
    ).distinct()


@address_list(
    'Unverified addresses - DO NOT USE',
    reason="because you are a registered user at pyweek.org."
)
def unverified_users(challenge=None):
    """Unverified e-mail accounts.

    Only use this to contact people to prompt them to verify their accounts.
    """
    return EmailAddress.objects.filter(
        user__settings__email_contest_updates=True,
        verified=False,
    ).distinct()


@address_list(
    'Previous participants',
    reason="because you are a previous Pyweek entrant."
)
def previous_participants():
    """A list of users who have participated in any previous challenge."""
    return filter_verified(EmailAddress.objects.filter(
        user__entry__has_final=True,
        user__settings__email_news=True,
    ).distinct())


@address_list(
    'Latest challenge entrants',
    reason="because you are an entrant in the latest Pyweek challenge."
)
def latest_challenge_users(challenge=None):
    """E-mail participants in the latest challenge."""
    challenge = challenge or Challenge.objects.latest()
    return filter_verified(EmailAddress.objects.filter(
        user__entry__challenge=challenge,
        user__settings__email_contest_updates=True,
    ).distinct())


@address_list(
    'Latest challenge non-finishers',
    reason="because you entered the latest Pyweek challenge."
)
def latest_challenge_dnf(challenge=None):
    """E-mail participants in the latest challenge who have never finished."""
    challenge = challenge or Challenge.objects.latest()
    return filter_verified(EmailAddress.objects.filter(
        user__entry__challenge=challenge,
        user__settings__email_contest_updates=True,
    ).exclude(
        user__entry__has_final=True,
    ).distinct())


@address_list(
    'Latest challenge finalists',
    reason="because you are an entrant in the latest Pyweek challenge."
)
def latest_challenge_finalists(challenge=None):
    """E-mail participants in the latest challenge with a final entry."""
    challenge = challenge or Challenge.objects.latest()
    return filter_verified(EmailAddress.objects.filter(
        user__entry__challenge=challenge,
        user__entry__has_final=True,
        user__settings__email_contest_updates=True,
    ).distinct())


@address_list(
    'Frequent entrants',
    reason="because you have participated in several Pyweek challenges."
)
def frequent_entrants():
    """E-mail participants who have participated 3 times or more."""
    return filter_verified(
    	EmailAddress.objects.annotate(
            num_entries=Count('user__entry__challenge', distinct=True)
    	).filter(
	    num_entries__gte=3,
            user__settings__email_contest_updates=True,
        ).distinct()
    )


@address_list(
    'Infrequent entrants',
    reason="because you are a previous Pyweek entrant."
)
def infrequent_entrants():
    """E-mail participants who have participated once or twice."""
    return filter_verified(
    	EmailAddress.objects.annotate(
            num_entries=Count('user__entry__challenge', distinct=True)
    	).filter(
	    num_entries__gte=1,
	    num_entries__lt=3,
            user__settings__email_contest_updates=True,
        ).distinct()
    )


@address_list(
    'Staff',
    reason="because you are a Pyweek organiser."
)
def staff():
    """E-mail staff."""
    return filter_verified(EmailAddress.objects.filter(user__is_staff=True))


@address_list(
    'Site admins',
    reason="because you are listed in settings.ADMINS."
)
def admins():
    admin_addresses = {addr for name, addr in settings.ADMINS}
    return EmailAddress.objects.filter(
        user__email__in=admin_addresses,
        user__is_superuser=True,
    )


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
