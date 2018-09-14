import time
import datetime
import smtplib
import random

from django.core.management.base import BaseCommand, CommandError

from pyweek.challenge.models import Challenge, Entry, UTC


def send_email(challenge, message, **info):
    info.update(dict(
        ch=challenge.title,
        chnum=challenge.number
    ))

    message += '''

     Daniel Pope
     https://pyweek.org/

----
You are receiving this email because you have signed up to the PyWeek
challenge as an entrant. If you do not wish to receive emails of this
kind please reply to the message asking to be removed. And accept my
apologies in advance.
'''
    emails = set()
    for entry in Entry.objects.filter(challenge=challenge):
       for user in entry.users.all():
          emails.add(user.email)
    #emails = set(['r1chardj0n3s@gmail.com', 'rjones@ekit-inc.com'])
    for email in emails:
        info['to'] = email
        # send email
        s = smtplib.SMTP()
        s.connect('localhost')
        try:
             s.sendmail('richard@pyweek.org', [email], message%info)
             s.close()
        except EnvironmentError, e:
             print 'EMAIL %s: %s' % (email, e)
        else:
             print 'EMAIL %s' % (email, )
        time.sleep(.1)


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
From: Richard Jones <richard@pyweek.org>
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
    def handle(self, *args, **options):
        all = list(Challenge.objects.filter(number__lt=1000))
        latest = all[-1]

        sd = latest.start_utc()
        ed = latest.end_utc()
        sv = sd - datetime.timedelta(7)
        dd = ed + datetime.timedelta(14)

        now = datetime.datetime.now(UTC)

        # just in case cron fires us before 00:00:00
        while now.hour != 0:
            time.sleep(1)
            now = datetime.datetime.now(UTC)

        nd = now.date()

        if nd == sv.date():
            latest.theme_poll.is_open = True
            latest.theme_poll.is_hidden = False
            latest.theme_poll.save()
            options = list(latest.theme_poll.option_set.all())
            random.shuffle(options)
            themes = '\n'.join(['- %s'%o.text for o in options])
            url = 'http://pyweek.org/p/%s/'%latest.theme_poll.id
            print 'PYWEEK BOT: SENDING VOTING EMAIL'
            send_email(latest, VOTING_START, themes=themes, poll_url=url)
            print 'PYWEEK BOT: SENT VOTING EMAIL'
        elif nd == sd.date():
            # this also closes the poll
            theme = latest.setTheme()
            send_email(latest, CHALLENGE_START, theme=theme)
            print 'PYWEEK BOT: SENT CHALLENGE START EMAIL'
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

