from django.core import mail
from datetime import date, datetime, timedelta
from django.test import TestCase
from django.contrib.auth.models import User

from .models import Challenge


class ChallengeTest(TestCase):
    def test_create_challenge(self):
        """We can create a new challenge"""
        c = Challenge.objects.create(
            title='June 2012',
            start=date(2012, 6, 4),
            end=date(2012, 6, 11),
        )
        # We get assigned a number (needed for admin)
        assert c.number == 1

    def test_challenge_numbering(self):
        """New challenges get assigned numbers."""
        for i in range(3):
            c = Challenge.objects.create(
                title='June 2012',
                start=date(2012, 6, 4),
                end=date(2012, 6, 11),
            )
            assert c.number == i + 1

    def test_homepage(self):
        """An upcoming challenge shows on the homepage."""
        Challenge.objects.create(
            title='July 2112',
            start=date(2112, 7, 31),
            end=date(2112, 8, 6),
        )
        resp = self.client.get('/')
        self.assertContains(resp, 'July 2112')
        self.assertContains(resp, 'Registration will be open 30 days before it starts.')


class RegistrationTest(TestCase):
    """Test accounts"""

    def test_register_link_disabled(self):
        resp = self.client.get('/')
        self.assertNotContains(resp, 'Register')

    def test_register_forbidden(self):
        """Users cannot register if there are no challenges."""
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 403)

    def test_register_link_upcoming_challenge(self):
        today = date.today()
        end = today + timedelta(days=7)
        Challenge.objects.create(
            title='July 2013',
            start=today,
            end=end
        )
        resp = self.client.get('/')
        self.assertContains(resp, 'Register')

    def test_register_upcoming_challenge(self):
        """Users can register if there is an upcoming challenge"""
        today = date.today()
        end = today + timedelta(days=7)
        Challenge.objects.create(
            title='July 2013',
            start=today,
            end=end
        )
        resp = self.client.get('/register/')
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Registration Form')
        self.assertContains(resp, '<form')

    def register(self):
        """Helper method to attempt a registration."""
        resp = self.client.post('/register/', {
            'name': 'atestuser',
            'email': 'atest@example.com',
            'password': 'test',
            'again': 'test'
        }, follow=True)
        return resp

    def test_do_register_no_upcoming_challenge(self):
        """We cannot register if there is no upcoming challenge."""
        resp = self.register()
        self.assertEqual(resp.request['PATH_INFO'], '/register/')
        self.assertContains(resp, 'Registration is currently closed.')

    def test_do_register(self):
        """We can register if there is an upcoming challenge."""
        today = date.today()
        end = today + timedelta(days=7)
        Challenge.objects.create(
            title='July 2013',
            start=today,
            end=end
        )
        resp = self.register()
        self.assertEqual(resp.request['PATH_INFO'], '/')
        self.assertContains(resp, 'Welcome to the Challenge!')



class LoginTest(TestCase):
    fixtures = ['testuser.json']

    def test_login_form(self):
        """The login form is usable"""
        resp = self.client.get('/login/')
        self.assertContains(resp, '<form class="form" action="" method="post">', html=True)
        self.assertContains(resp, '<input id="id_username" type="text" maxlength="30" name="username">', html=True)

    def test_login(self):
        """Users can login"""
        self.client.get('/login/')
        resp = self.client.post('/login/', {
            'username': 'test',
            'password': 'password'
        })
        self.assertEqual(resp.status_code, 302)
        self.assertEqual(resp['Location'], 'http://testserver/')

    def test_invalid_password(self):
        """Users cannot login if their password is invalid."""
        self.client.get('/login/')
        resp = self.client.post('/login/', {
            'username': 'test',
            'password': 'afdag'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

    def test_invalid_creds(self):
        """Users cannot login if their credentials are invalid."""
        self.client.get('/login/')
        resp = self.client.post('/login/', {
            'username': 'werijw',
            'password': 'afdag'
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Invalid username or password')

    def test_forgotten_password(self):
        """Users can enter their e-mail address to receive a notification."""
        resp = self.client.post('/resetpw/', {
            'email_address': 'test@example.com'
        }, follow=True)
        self.assertContains(resp, 'Email sent to test@example.com')
        self.assertEqual(mail.outbox[0].subject, 'Your PyWeek login details')

    def test_forgotten_password_missing_email(self):
        "Submitting the lost password form without an address gives an error"
        resp = self.client.post('/resetpw/', {})
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'This field is required.')

    def test_forgotten_password_bad_address(self):
        resp = self.client.post('/resetpw/', {
            'email_address': 'bob@nosuchsite.com',
        })
        self.assertEqual(resp.status_code, 200)
        self.assertContains(resp, 'Email address not recognised')


class LogoutTest(TestCase):
    fixtures = ['testuser.json']

    def setUp(self):
        self.client.get('/login/')
        self.client.post('/login/', {
            'username': 'testuser',
            'password': 'password'
        })

    def test_logout_link(self):
        resp = self.client.get('/')
        self.assertContains(resp, '<a href="/logout/">', html=True)

    def test_logout(self):
        """Users can logout"""
        resp = self.client.get('/logout/')
        self.assertEqual(resp.status_code, 302)

        resp = self.client.get('/')
        self.assertContains(resp, 'Login')
        self.assertContains(resp, 'Not logged in')


class DiscussionTest(TestCase):
    def test_new_thread(self):
        """Users can start a new thread."""

    def test_thread_list(self):
        """New threads appear in the list"""

    def test_thread_pagination(self):
        """Threads are displated in pages."""

    def test_comment(self):
        """Users can post comments on existing threads."""




class TimetableTest(TestCase):
    def test_timetable(self):
        start = date(2012, 05, 06)
        c = Challenge(start=start)
        self.assertEqual(c.timetable(), [
            (datetime(2012, 4, 6), 'Pre-registration underway'),
            (datetime(2012, 4, 29), 'Theme voting commences'),
            (datetime(2012, 5, 6), 'Challenge start'),
            (datetime(2012, 5, 13), 'Challenge end, judging begins'),
            (datetime(2012, 5, 27), 'Judging closes, winners announced'),
        ])
