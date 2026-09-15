import datetime

from django.contrib.auth.models import User
from django.test import TestCase

from pyweek.challenge.models import Challenge, Entry
from pyweek.users.models import EmailAddress
from .lists import filter_verified, latest_challenge_non_entrants
from .models import DraftEmail
from .views import mailing_list_choices


class NonEntrantMailingListTests(TestCase):
    def setUp(self):
        self.previous = Challenge.objects.create(
            number=41, title='Previous', start=datetime.date(2025, 3, 1),
            end=datetime.date(2025, 3, 8),
        )
        self.current = Challenge.objects.create(
            number=42, title='Current', start=datetime.date(2025, 9, 1),
            end=datetime.date(2025, 9, 8),
        )

    def address(self, name, verified=True, news=True):
        user = User.objects.create(username=name)
        user.settings.email_news = news
        user.settings.save()
        return EmailAddress.objects.create(
            user=user, address=f'{name}@example.com', verified=verified,
        )

    def enter(self, challenge, name, *addresses):
        entry = Entry.objects.create(name=name, title=name, challenge=challenge,
                                     user=addresses[0].user)
        entry.users.add(*(address.user for address in addresses))
        return entry

    def test_audience_and_form_choice(self):
        newcomer = self.address('newcomer')
        returning = self.address('returning')
        owner = self.address('owner')
        teammate = self.address('teammate')
        unverified = self.address('unverified', verified=False)
        unverified.user.email = unverified.address
        unverified.user.save()
        self.address('unsubscribed', news=False)
        self.enter(self.previous, 'old', returning, owner)
        self.enter(self.previous, 'older', returning)
        self.enter(self.current, 'current', owner, teammate)
        # Contest updates concern existing entrants, not invitations to enter.
        newcomer.user.settings.email_contest_updates = False
        newcomer.user.settings.save()
        draft = DraftEmail(list_name='latest_challenge_non_entrants')
        self.assertCountEqual(draft.recipients, [newcomer, returning])
        self.assertIn(
            ('latest_challenge_non_entrants',
             'Latest challenge non-entrants (verified) (2 recipients)'),
            mailing_list_choices(),
        )
        self.assertIn('have not entered', draft.list_reason)
        self.enter(self.current, 'new-entry', newcomer)
        self.assertCountEqual(draft.recipients, [returning])

    def test_explicit_challenge(self):
        previous_entrant = self.address('previous')
        current_entrant = self.address('current')
        self.enter(self.previous, 'old', previous_entrant)
        self.enter(self.current, 'new', current_entrant)
        self.assertCountEqual(
            latest_challenge_non_entrants(self.previous), [current_entrant],
        )

    def test_no_challenge_has_no_recipients(self):
        Challenge.objects.all().delete()
        self.address('newcomer')
        self.assertFalse(latest_challenge_non_entrants().exists())

    def test_legacy_primary_address_requires_verification(self):
        address = self.address('legacy', verified=False)
        address.user.email = address.address
        address.user.save()
        self.assertFalse(filter_verified(EmailAddress.objects.all()).exists())
        address.verified = True
        address.save()
        self.assertCountEqual(filter_verified(EmailAddress.objects.all()), [address])
