from datetime import datetime, timedelta
from unittest.mock import PropertyMock, patch

from django.contrib.auth.models import Permission, User
from django.test import TestCase
from django.urls import reverse

from .models import DraftEmail


class EmailHistoryTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username='organiser')
        self.user.user_permissions.add(Permission.objects.get(
            content_type__app_label='mail', codename='add_draftemail',
        ))
        self.client.force_login(self.user)
        self.sent = DraftEmail.objects.create(
            list_name='announce', subject='Previous announcement',
            body='<p>Saved announcement body</p>',
            status=DraftEmail.STATUS_SENT, sent=datetime(2026, 1, 1),
        )
        self.draft = DraftEmail.objects.create(
            list_name='announce', subject='Unsent draft', body='<p>Draft</p>',
        )

    def test_history_is_newest_first_and_paginated(self):
        for i in range(31):
            DraftEmail.objects.create(
                list_name='announce', subject=f'Sent message {i}', body='Body',
                status=DraftEmail.STATUS_SENT,
                sent=self.sent.sent + timedelta(days=i + 1),
            )
        DraftEmail.objects.create(
            list_name='announce', subject='Still sending', body='Body',
            status=DraftEmail.STATUS_SENDING,
        )
        response = self.client.get(reverse('sent-emails'))
        self.assertContains(response, 'Sent message 30')
        self.assertNotContains(response, self.draft.subject)
        self.assertNotContains(response, 'Still sending')
        self.assertEqual(response.context['paginator'].count, 32)
        self.assertEqual(response.context['object_list'][0].subject, 'Sent message 30')
        self.assertContains(response, '?page=2')
        response = self.client.get(reverse('sent-emails'), {'page': 2})
        self.assertContains(response, self.sent.subject)
        self.assertContains(response, self.sent.get_absolute_url())
        self.assertContains(response, '?page=1')

    def test_drafts_link_to_history_but_exclude_sent_messages(self):
        response = self.client.get(reverse('draft-emails'))
        self.assertContains(response, self.draft.subject)
        self.assertNotContains(response, self.sent.subject)
        self.assertContains(response, reverse('sent-emails'))

    def test_sent_previews_are_read_only_without_current_recipient_counts(self):
        # Historical previews must not evaluate a mailing list that changes over time.
        with patch.object(
            DraftEmail, 'recipients', new_callable=PropertyMock,
            side_effect=AssertionError('Historical preview evaluated current recipients'),
        ):
            for name in ('preview-email', 'preview-email-text'):
                with self.subTest(view=name):
                    response = self.client.get(reverse(name, args=[self.sent.pk]))
                    self.assertContains(response, 'Saved announcement body')
                    self.assertContains(response, 'Sent:')
                    self.assertContains(response, reverse('sent-emails'))
                    self.assertNotContains(response, reverse('edit-email', args=[self.sent.pk]))
                    self.assertNotContains(response, '<button>Send</button>')
                    self.assertNotContains(response, ' recipients)')

    def test_sent_email_cannot_be_edited_or_resent(self):
        edit_url = reverse('edit-email', args=[self.sent.pk])
        self.assertEqual(self.client.get(edit_url).status_code, 404)
        self.assertEqual(self.client.post(edit_url, {'subject': 'Changed'}).status_code, 404)
        with patch('pyweek.mail.views.sending.send') as send:
            self.client.post(reverse('send-email', args=[self.sent.pk]))
            send.assert_not_called()
        self.sent.refresh_from_db()
        self.assertEqual(self.sent.subject, 'Previous announcement')

    def test_history_requires_existing_email_permission(self):
        self.user.user_permissions.clear()
        for url in (reverse('sent-emails'), self.sent.get_absolute_url()):
            self.assertEqual(self.client.get(url).status_code, 403)
        self.client.logout()
        self.assertEqual(self.client.get(reverse('sent-emails')).status_code, 302)

    def test_empty_history(self):
        self.sent.delete()
        self.assertContains(self.client.get(reverse('sent-emails')), 'No sent e-mails.')
