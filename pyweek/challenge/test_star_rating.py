"""STAR ballot fallback and submission regression tests."""
from django.contrib.auth.models import User
from django.test import TestCase
from pyweek.challenge.models import Challenge, Poll, Option, Response
from pyweek.challenge.views.poll import choice_field


class StarRatingTests(TestCase):
    def setUp(self):
        challenge = Challenge.objects.create(number=42, title='Test', start='2026-09-20', end='2026-09-27')
        self.poll = Poll.objects.create(challenge=challenge, title='Theme', description='', is_open=True, is_hidden=False, is_ongoing=True, type=Poll.STAR_VOTE)
        self.options = [Option.objects.create(poll=self.poll, text=text) for text in ('A < B', 'Second')]
        self.user = User.objects.create_user(username='voter')
        self.client.force_login(self.user)
        self.url = f'/p/{self.poll.pk}/'

    def test_fallback_is_labelled_required_and_unrated(self):
        response = self.client.get(self.url)
        self.assertContains(response, 'data-star-rating value=""', count=2)
        self.assertContains(response, f'<label for="vote-{self.options[0].pk}">A &lt; B</label>')
        self.assertContains(response, 'type="number" min="0" max="5" step="1" required', count=2)
        self.assertContains(response, 'js/star-rating.js')

    def test_zero_and_five_round_trip(self):
        values = {f'vote-{option.pk}': str(value) for option, value in zip(self.options, (0, 5))}
        response = self.client.post(self.url, values)
        self.assertContains(response, 'Vote recorded')
        self.assertEqual(list(Response.objects.filter(poll=self.poll).order_by('option_id').values_list('value', flat=True)), [0, 5])
        response = self.client.get(self.url)
        self.assertContains(response, 'data-star-rating value="0"')
        self.assertContains(response, 'data-star-rating value="5"')

    def test_other_poll_inputs_are_not_enhanced(self):
        for poll_type in (Poll.POLL, Poll.INSTANT_RUNOFF, Poll.BEST_TEN, Poll.SELECT_MANY):
            self.poll.type = poll_type
            self.assertNotIn('data-star-rating', choice_field(self.poll, self.options[0].pk, {}))
