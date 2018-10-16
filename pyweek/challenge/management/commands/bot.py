import re
import time
import datetime
import smtplib
import random

from django.db.models import Q
from django.contrib.auth.models import User
from django.core.management.base import BaseCommand, CommandError

from pyweek.users.models import EmailAddress
from pyweek.challenge.models import Challenge, Entry, UTC
from pyweek.activity.models import log_event
from pyweek.mail.lists import latest_challenge_users
from pyweek.mail import sending
from django.template.defaultfilters import urlize, linebreaks


def send_email(challenge, message, **info):
    info.update(dict(
        ch=challenge.title,
        chnum=challenge.number,
        to='',
    ))
    message = message % info
    hdrs, body = message.split('\n\n', 1)

    mo = re.match(r'^Subject: *([^\n]+)', hdrs)
    if not mo:
        raise Exception('Failed to parse message')

    mailing_list = set(e.address for e in latest_challenge_users(challenge))

    html_body = linebreaks(urlize(body))

    sending.send(
        subject=mo.group(1),
        html_body=html_body,
        recipients=mailing_list,
        reason=latest_challenge_users.reason,
        priority=sending.PRIORITY_HIGH,
    )


CHALLENGE_DONE = '''Subject: PyWeek %(ch)s is over!
From: Richard Jones <richard@pyweek.org>
To: %(to)s

PyWeek %(ch)s - "%(theme)s" is over, the scores are in and the winners are:

%(winner)s

Congratulations to everyone who entered!

Now that judging is over you may upload updated versions of your games.

See you in six months!

Don't forget that in the mean time you might like to enter the
pyggy awards, or the pyday contests.
'''

CHALLENGE_END = '''Subject: Programming for PyWeek %(ch)s has ended!
From: Richard Jones <richard@pyweek.org>
To: %(to)s

Pens up! %(ch)s - "%(theme)s" - progamming time has ended!

You now have 24 hours to upload your game and 2 weeks to play
and rate everyone else's games.
'''

CHALLENGE_START = '''Subject: PyWeek %(ch)s has started!
From: Daniel Pope <daniel@pyweek.org>
To: %(to)s

%(ch)s has started!

The theme for this challenge is "%(theme)s".

Please make sure you've had a read of the rules and help pages.
In particular make sure you're aware of the rules for submissions:

  https://pyweek.org/s/rules/
  https://pyweek.org/s/help/

Don't forget that there's a diary attached to your entry - record
your progress and upload screenshots! Diary entries are displayed
in the challenge page:

  https://pyweek.org/%(chnum)s/diaries/

Finally there's a handy reference listing links to game development
resources (theory, artwork, music, ...) on the Discussion page:

  https://pyweek.org/messages/

Good luck!
'''


VOTING_START = '''Subject: Theme voting for PyWeek %(ch)s has commenced!
From: Daniel Pope <daniel@pyweek.org>
To: %(to)s

Welcome to %(ch)s!

Voting for the theme of %(ch)s has commenced!

The theme choices are:

%(themes)s

You may find the poll on the website at:

%(poll_url)s

If this is your first PyWeek I recommend you have a read through the rules and help pages. They won't take too long and have valuable information:

  http://pyweek.org/s/rules/
  http://pyweek.org/s/help/


Stay a while ... stay forever!
'''

class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            '--force-date',
            dest='date',
            help='Override the date we are running for.'
        )

    def handle(self, *args, **options):
        latest = Challenge.objects.latest()

        sd = latest.start_utc()
        ed = latest.end_utc()
        sv = sd - datetime.timedelta(7)
        dd = ed + datetime.timedelta(14)

        date = options.get('date')
        if date:
            nd = datetime.datetime.strptime(date, '%Y-%m-%d').date()
        else:
            # No date given, use current date and wait till midnight
            now = datetime.datetime.now(UTC)
            # just in case cron fires us before 00:00:00
            while now.hour != 0:
                time.sleep(1)
                now = datetime.datetime.now(UTC)
            nd = now.date()

        if nd == sv.date():
            self.begin_theme_voting(latest)
        elif nd == sd.date():
            self.start_challenge(latest)
        elif nd == ed.date():
            theme = latest.getTheme()
            send_email(latest, CHALLENGE_END, theme=theme)
            print 'PYWEEK BOT: SENT CHALLENGE END EMAIL'
        elif nd == dd.date():
            latest.generate_tallies()
            theme = latest.getTheme()
            winner = []
            for e in latest.individualWinners():
                title = e.game or e.title
                winner.append('Individual: %s (http://pyweek.org/e/%s)'%(title, e.name))
            for e in latest.teamWinners():
                title = e.game or e.title
                winner.append('Team: %s (http://pyweek.org/e/%s)'%(title, e.name))
            winner = '\n'.join(winner)
            send_email(latest, CHALLENGE_DONE, theme=theme, winner=winner)
            print 'PYWEEK BOT: SENT CHALLENGE ALL DONE'
        else:
            print 'PYWEEK BOT: DID NOTHING'


    def begin_theme_voting(self, latest):
        latest.theme_poll.is_open = True
        latest.theme_poll.is_hidden = False
        latest.theme_poll.save()
        options = list(latest.theme_poll.option_set.all())

        themes = '\n'.join(['- %s'%o.text for o in options])
        url = 'http://pyweek.org/p/%s/'%latest.theme_poll.id
        print 'PYWEEK BOT: SENDING VOTING EMAIL'
        send_email(latest, VOTING_START, themes=themes, poll_url=url)
        print 'PYWEEK BOT: SENT VOTING EMAIL'
        log_event(
            type="theme-voting",
            target=latest.theme_poll,
            challenge_number=latest.number,
            challenge_title=latest.title,
            options=[o.text for o in options],
        )
        print 'PYWEEK BOT: Posted to activity log'

    def start_challenge(self, latest):
        theme = latest.setTheme()  # this also closes the poll
        send_email(latest, CHALLENGE_START, theme=theme)
        print 'PYWEEK BOT: SENT CHALLENGE START EMAIL'
        log_event(
            type="challenge-start",
            target=latest,
            challenge_number=latest.number,
            challenge_title=latest.title,
            theme=theme,
            poll_id=latest.theme_poll.id,
        )
        print 'PYWEEK BOT: Posted to activity log'
