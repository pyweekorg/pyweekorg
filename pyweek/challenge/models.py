import os
import operator

from django.conf import settings
from django.core import validators
from django.db import models, connection, transaction
from django.contrib.auth.models import User
from django.urls import reverse
from django.db.models.signals import pre_save
from django.utils.timezone import now

from ..activity.models import EventRelation


from pyweek.bleaching import html2text
import datetime

# Maximum number of checksums per entry. Set to None to disable
MAX_CHECKSUMS = 5

# Time before the deadline when we switch to MD5-only
CUTOFF_TIME = 2*60*60

# Number of days allowed to upload against MD5
EXTRA_DAYS = 3

UTC = datetime.timezone.utc


def pretty_time_diff(diff: datetime.timedelta) -> str:
    minutes = diff.seconds // 60
    hours, minutes = divmod(minutes, 60)

    l = []

    if diff.days > 1:
        l.append(f'{int(diff.days)} days')
    if diff.days == 1:
        l.append('1 day')
    if hours > 1:
        l.append(f'{int(hours)} hours')
    if hours == 1:
        l.append('1 hour')
    if minutes > 1:
        l.append(f'{int(minutes)} minutes')
    if minutes == 1:
        l.append('1 minute')
    if not l:
        l.append('less than 1 minute')
    if len(l) == 1:
        return l[0]

    *rest, last = l
    return ', '.join(rest) + f' and {last}'


def participation():
    cursor = connection.cursor()

    # generate stats on participation
    data = {
        1: {'users': 155, 'entries': 110, 'finals': 26},
    }
    sql = '''
    select challenge_id, count(distinct(u.user_id))
    from challenge_entry,challenge_entry_users u, challenge_challenge c
    where entry_id=challenge_entry.name
      and c.number=challenge_id
      and challenge_id<1000
      and c.end < now() - interval '1 day'
    group by challenge_id '''
    cursor.execute(sql)
    for row in cursor.fetchall():
        data[row[0]] = {'users': row[1]}

    sql = '''
    select challenge_id, count(*)
      from challenge_entry, challenge_challenge c
     where challenge_id<1000
      and c.number=challenge_id
      and c.end < now() - interval '1 day'
    group by challenge_id'''
    cursor.execute(sql)
    for row in cursor.fetchall():
        data[row[0]]['entries'] = row[1]

    sql = '''
    select challenge_id, count(*)
      from challenge_entry, challenge_challenge c
     where challenge_id<1000
       and has_final=true
       and c.number=challenge_id
       and c.end < now() - interval '1 day'
    group by challenge_id'''
    cursor.execute(sql)
    for row in cursor.fetchall():
        data[row[0]]['finals'] = row[1]

    return data


class ChallengeManager(models.Manager):
    def get_latest_and_previous(self):
        cs = list(self.pyweek_challenges().order_by('-start')[:2])
        return cs + [None] * (2 - len(cs))

    def latest(self):
        """Get the latest challenge."""
        return self.get_latest_and_previous()[0]

    def previous(self):
        """Get the previous challenge."""
        return self.get_latest_and_previous()[1]

    def all_previous(self):
        """Get a QuerySet of all challenges that have finished."""
        today = datetime.date.today()
        return self.pyweek_challenges().filter(end__lt=today).order_by('-start')

    def pyweek_challenges(self):
        """All Pyweek challenges.

        AFAICT challenge numbers >1000 are reserved for Pyggys.

        """
        return self.filter(number__lt=1000)



class Challenge(models.Model):
    number = models.IntegerField(primary_key=True)
    title = models.CharField(max_length=100)
    start = models.DateField()
    end = models.DateField()
    motd = models.TextField()
    is_rego_open = models.BooleanField(
        default=False,
        help_text=(
            "Set to True to open registration for this competition now. "
            "Otherwise, registration opens {days} days before the "
            "competition.".format(days=settings.REGISTRATION_OPENS)
        )
    )
    theme_poll = models.ForeignKey(
        'Poll',
        null=True,
        blank=True,
        related_name='poll_challenge',
        on_delete=models.SET_NULL,  # Deleting a poll doesn't impact the challenge
    )
    theme = models.CharField(max_length=100, null=True, blank=True, default='')
    torrent_url = models.CharField(max_length=255, null=True, blank=True, default='')

    objects = ChallengeManager()

    class Meta:
        ordering = ['start']

    def __repr__(self):
        return f'<{self}>'

    def __str__(self):
        return f'Challenge {int(self.number)}: {self.title!r}'

    def get_absolute_url(self):
        return f'/{int(self.number)}/'

    @property
    def rules(self):
        """Get a dict of specify rules by competition number."""
        return {
            # True if ratings are associated with the username
            'ratings_public': 25 < self.number < 1000,
        }

    def start_utc(self):
        return datetime.datetime(self.start.year, self.start.month,
            self.start.day, 0, 0, 0, 0)

    def end_utc(self):
        return datetime.datetime(self.end.year, self.end.month, self.end.day,
            0, 0, 0, 0)

    def countdown(self):
        now = datetime.datetime.utcnow()
        sd = self.start_utc()
        ed = self.end_utc()
        if now < sd:
            diff = sd - now
            event = 'challenge start'
        elif now < ed:
            diff = ed - now
            event = 'challenge end'
        elif now < ed + datetime.timedelta(14):
            diff = ed - now + datetime.timedelta(14)
            event = 'judging ends'
        else:
            return 'challenge finished'
        return f'{event}: {pretty_time_diff(diff)}'

    def summary(self):
        now = datetime.datetime.utcnow()
        sv = self.start_utc() - datetime.timedelta(7)
        sd = self.start_utc()
        ed = self.end_utc()
        if now < sv:
            diff = sd - now
            event = [f'The {self.title} challenge starts in', '', '']
        elif now < sd:
            diff = sd - now
            event = ['Theme voting; challenge starts in', '',
                f'(<a href="/p/{self.theme_poll.id}">vote</a>)']
        elif now < ed:
            diff = ed - now
            event = [f'"{self.getTheme()}" challenge underway;',
                '', 'to go']
        elif now < ed + datetime.timedelta(1):
            diff = ed - now + datetime.timedelta(1)
            event = [f'"{self.getTheme()}" challenge is finished;', '', 'to upload your entry']
        elif now < ed + datetime.timedelta(14):
            diff = ed - now + datetime.timedelta(14)
            event = ['Judging ends in', '', '']
        else:
            return f'"{self.getTheme()}" challenge is finished'

        event[1] = pretty_time_diff(diff)
        return ' '.join(event)

    def setTheme(self):
        # close the poll
        poll = self.theme_poll
        poll.is_open = False
        poll.save()

        # and save off the winner
        self.theme = poll.instant_runoff_winner()
        self.save()
        return self.theme

    def getTheme(self):
        if self.theme:
            return self.theme
        else:
            return '[not chosen yet]'

    def pageTitle(self):
        if self.theme:
            return f'PyWeek &mdash; {self.title} &mdash; {self.theme}'
        else:
            return f'PyWeek &mdash; {self.title}'

    def registration_start(self):
        """The date on which registration opens."""
        DAY = datetime.timedelta(days=1)
        return self.start_utc() - settings.REGISTRATION_OPENS * DAY

    def isCompComing(self):
        """Competition has been created but is still long in the future."""
        if self.is_rego_open:  # overridden by admin
            return False
        rego_date = self.registration_start()
        now = datetime.datetime.utcnow()
        return now < rego_date

    def isRegoOpen(self):
        """Are we in the registration window for this challenge?"""
        if self.is_rego_open and not self.isCompFinished():  # overridden by admin
            return True
        now = datetime.datetime.utcnow()
        sd = self.start_utc()
        ed = self.end_utc() + datetime.timedelta(1)
        rego_date = self.registration_start()
        end_rego_date = ed
        return rego_date <= now <= end_rego_date

    def isVotingOpen(self):
        if not self.theme_poll:
            return False
        sd = self.start_utc() - datetime.timedelta(7)
        ed = self.start_utc()
        now = datetime.datetime.utcnow()
        return sd <= now < ed

    def isCompStarted(self):
        sd = self.start_utc()
        now = datetime.datetime.utcnow()
        return now >= sd

    def isCompRunning(self):
        sd = self.start_utc()
        ed = self.end_utc()
        now = datetime.datetime.utcnow()
        return sd <= now <= ed

    def isCompFinished(self):
        ed = self.end_utc()
        now = datetime.datetime.utcnow()
        return now > ed

    def isUploadOpen(self):
        '''File upload is allowed in the following time range:

        from the start date to 24 hours after the end date
        from the end of judging onwards
        '''
        sd = self.start_utc()
        ed = self.end_utc() + datetime.timedelta(1)
        now = datetime.datetime.utcnow()
        end_date = ed + datetime.timedelta(13)
        ret = sd <= now <= ed or now > end_date
        return ret

    def isFinalUploadOpen(self):
        '''FINAL file upload is allowed in the following time range:

        from the start date to 24 hours after the end date
        '''
        sd = self.start_utc()
        ed = self.end_utc() + datetime.timedelta(15)
        now = datetime.datetime.utcnow()
        ret = sd <= now <= ed
        return ret

    def isGraceUploadTime(self):
        '''FINAL file upload during the 24 hours after the end date
        '''
        sd = self.end_utc()
        ed = self.end_utc() + datetime.timedelta(1)
        now = datetime.datetime.utcnow()
        return sd <= now <= ed

    def isRatingOpen(self):
        ed = self.end_utc() + datetime.timedelta(1)
        now = datetime.datetime.utcnow()
        end_date = self.end_utc() + datetime.timedelta(14)
        return ed < now <= end_date

    def isAllDone(self):
        ed = self.end_utc()
        now = datetime.datetime.utcnow()
        end_date = ed + datetime.timedelta(14)
        return now > end_date

    def timetableHTML(self):
        ''' Generate HTML rows for a timetable display. '''
        l = []
        now = datetime.datetime.utcnow()
        def add(this, next, event):
            style = None
            if this <= now < next or (this <= now and next is None):
                style = 'active'
                event = event.split()
                event = ' '.join(event[:-1] + ['underway'])
            elif next is not None and now >= next:
                style = 'done'
            date = this.strftime('%A %Y/%m/%d')
            if style:
                l.append(f'<tr class="{style}"><td>{date}</td><td>{event}</td>')
            else:
                l.append(f'<tr><td>{date}</td><td>{event}</td>')
        rego_date = self.registration_start()
        sd = self.start_utc()
        ed = self.end_utc()
        this, next = rego_date, sd - datetime.timedelta(7)
        add(this, next, 'Pre-registration open')
        this, next = next, sd
        add(this, next, 'Theme voting commences')
        this, next = next, ed
        add(this, next, 'Challenge start')
        this, next = next, ed + datetime.timedelta(14)
        add(this, next, 'Challenge end, judging begins')
        add(next, None, 'Judging closes, winners announced')
        return '\n'.join(l)

    @property
    def challenge(self):
        """The related name for 'entries' used to be set as 'challenge'.

        This alias is for backwards compatibility now that has been fixed.
        """
        return self.entries

    @transaction.atomic
    def generate_tallies(self):
        """Recalculate rating tallies for this challenge."""
        team = []
        individual = []
        for entry in self.entries.all():
            entry.ratingtally_set.all().delete()
            if not entry.has_final:
                continue

            ratings = entry.tally_ratings()
            ratingtally = RatingTally(
                challenge=self,
                entry=entry,
                individual=not entry.is_team(),
                fun=ratings['fun'],
                innovation=ratings['innovation'],
                production=ratings['production'],
                overall=ratings['overall'],
                nonworking=int(ratings['nonworking'] *100),
                disqualify=int(ratings['disqualify'] * 100),
                respondents=ratings['respondents'],
            )
            ratingtally.save()

            if entry.is_team():
                team.append((int(ratings['overall'] * 100), entry))
            else:
                individual.append((int(ratings['overall'] * 100), entry))

        # figure the winners
        by_score = operator.itemgetter(0)
        team.sort(key=by_score)
        individual.sort(key=by_score)
        for l in (team, individual):
            if not l:
                continue

            n = l[-1][0]
            for s, e in l:
                if s == n:
                    e.winner = self
                    e.save()

    def individualWinners(self):
        return [e for e in Entry.objects.filter(winner=self.number) if not e.is_team()]

    def teamWinners(self):
        return [e for e in Entry.objects.filter(winner=self.number) if e.is_team()]


def challenge_save(sender, instance, **kwargs):
    """Generate an instance number.

    This should be done at the database level, but would require a PostgreSQL
    SEQUENCE to be explicitly set up, which is much more difficult in Django.

    """
    if instance.number is None:
        try:
            instance.number = sender.objects.order_by('-number')[0].number + 1
        except IndexError:
            instance.number = 1

pre_save.connect(challenge_save, sender=Challenge)


class Entry(models.Model):
    SHORT_TITLE_LEN = 14

    name = models.SlugField(max_length=15, primary_key=True)
    title = models.CharField(
        max_length=100,
        help_text="The name of the team that created the entry."
    )
    game = models.CharField(
        max_length=100,
        help_text="The name of the game itself."
    )
    github_repo = models.CharField(
        max_length=81,
        blank=True,
        null=True,
        unique=True,
    )
    # sha1 of the HEAD commit
    head_sha = models.CharField(
        max_length=40,
        blank=True,
        null=True,
    )

    description = models.TextField()

    is_open = models.BooleanField(
        default=False,
        help_text="Can people request to join the team?"
    )
    group_url = models.URLField(
        blank=True,
        null=True,
        help_text="Chat/group URL, visible only to participants."
    )

    challenge = models.ForeignKey(
        Challenge,
        related_name='entries',
        on_delete=models.PROTECT,  # Should not delete a challenge that has entries
    )
    winner = models.ForeignKey(
        Challenge,
        blank=True,
        null=True,
        related_name='winner',
        on_delete=models.SET_NULL,  # Protected by above, won't duplicate here
    )
    user = models.ForeignKey(
        User,
        verbose_name='entry owner',
        related_name="owner",
        null=True,
        on_delete=models.SET_NULL,  # Entries can be team entries; deleting one
                                    # user must not delete the entry
    )
    users = models.ManyToManyField(User)
    is_upload_open = models.BooleanField(default=False)
    has_final = models.BooleanField(default=False)

    join_requests = models.ManyToManyField(
        User,
        related_name='join_request_entries'
    )


    class Meta:
        ordering = ['-challenge', 'name']
        verbose_name_plural = "entries"
        unique_together = (("challenge", "name"), ("challenge", "title"))

    def __repr__(self):
        return f'<Entry {self.name!r}>'

    def __str__(self):
        return f'Entry "{self.name}"'

    def get_absolute_url(self):
        return f'/e/{self.name}/'

    @property
    def display_title(self):
        """Display the title of the game."""
        return self.game or self.title

    @property
    def short_title(self):
        if len(self.title) <= Entry.SHORT_TITLE_LEN:
            return self.title
        return f"{self.title[:Entry.SHORT_TITLE_LEN]}..."

    def is_team(self) -> bool:
        return len(self.users.all()) > 1

    def diary_entries(self):
        """Get a QuerySet of all diary entries.

        Entries will be annotated with the number of comments.

        """
        return self.diaryentry_set.annotate(
            num_comments=models.Count('diarycomment')
        )

    def isUploadOpen(self) -> bool:
        if self.is_upload_open:
            return True
        challenge = self.challenge
        return challenge.isUploadOpen()

    #def has_final(self):
        #return len(self.file_set.filter(is_final__exact=True,
            #is_screenshot__exact=False))

    def may_rate(self, user: User, challenge: Challenge = None) -> bool:
        # determine whether the current user is allowed to rate the entry
        if user.is_anonymous:
            return False
        if user in self.users.all():
            # Users may not rate their own entry
            return False
        username = user.username
        if challenge is None:
            challenge = self.challenge
        if not self.has_final:
            # Cannot rate an entry that does not have a final submission
            return False

        # Check that the rating user has their own final entry
        for e in Entry.objects.filter(challenge=self.challenge, users__username__exact=username):
            if e.has_final:
                return True
        return False

    def has_rated(self, user: User) -> bool:
        if user.is_anonymous:
            return False
        return len(self.rating_set.filter(user__username__exact=user.username)) > 0

    def tally_ratings(self):
        ratings = self.rating_set.all()
        info = {}
        for rating in 'fun innovation production disqualify nonworking overall'.split():
            info[rating] = 0
        n = 0
        for rating in ratings:
            info['disqualify'] += rating.disqualify
            info['nonworking'] += rating.nonworking
            if rating.nonworking:
                continue
            n += 1
            info['fun'] += rating.fun
            info['innovation'] += rating.innovation
            info['production'] += rating.production
        m = float(len(ratings))
        num_finished = sum(len(e.users.all())
                for e in Entry.objects.filter(challenge=self.challenge)
                    if e.has_final)
        if n:
            for rating in 'fun innovation production'.split():
                info[rating] /= float(n)
            info['disqualify'] /= float(num_finished)
            info['nonworking'] /= float(len(ratings))
            info['participants'] = len(ratings)/float(num_finished)
            info['overall'] = (info['fun'] + info['innovation'] +
                info['production'])/3
        info['respondents'] = n
        return info

RATING_CHOICES = ((1, 'Not at all'), (2,'Below average'),
    (3,'About average'), (4,'Above average'), (5,'Exceptional'))


class Rating(models.Model):
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE  # ratings are specific to entries
    )
    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL  # user deletion should not change ratings
    )

    fun, innovation, production = [
        models.PositiveIntegerField(choices=RATING_CHOICES, default=3)
        for _ in range(3)
    ]

    nonworking = models.BooleanField()
    disqualify = models.BooleanField()
    comment = models.TextField()
    created = models.DateTimeField(default=now)

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']
        unique_together = (("entry", "user"),)

    def __repr__(self):
        return f'{self.user!r} rating {self.entry!r}'
    def __str__(self):
        return f'{self.user} rating {self.entry}'


class RatingTally(models.Model):
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE  # If deleting a challenge, ratingtally is not important
    )
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE  # RatingTally is specific to an entry
    )
    individual = models.BooleanField()
    fun = models.FloatField()
    innovation = models.FloatField()
    production = models.FloatField()
    overall = models.FloatField()
    nonworking = models.PositiveIntegerField()
    disqualify = models.PositiveIntegerField()
    respondents = models.PositiveIntegerField()

    class Meta:
        ordering = ['challenge', 'individual', '-overall']
        verbose_name_plural = "RatingTallies"

    def __repr__(self):
        return f'{self.entry!r} rating tally'
    def __str__(self):
        return f'{self.entry} rating tally'


class DiaryEntryManager(models.Manager):
    def for_challenge(self, challenge):
        return self.with_comment_counts().filter(
            entry__challenge__number=challenge.number
        ).select_related('entry').order_by('-created')

    def with_comment_counts(self):
        return self.annotate(
            num_comments=models.Count('diarycomment')
        )


class DiaryEntry(models.Model):
    challenge = models.ForeignKey(
        Challenge,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # Deleting a challenge doesn't need to delete diaries
    )
    entry = models.ForeignKey(
        Entry,
        blank=True,
        null=True,
        on_delete=models.CASCADE,  # Deleting an entry should delete its diary entries
    )
    user = models.ForeignKey(
        User,
        related_name='author',
        on_delete=models.CASCADE,  # Deleting a user account should delete user activity
    )
    title = models.CharField(max_length=100)
    content = models.TextField()
    created = models.DateTimeField(default=now)
    edited = models.DateTimeField(blank=True, null=True)
    activity = models.DateTimeField(default=now)
    actor = models.ForeignKey(
        User,
        related_name='actor',
        null=True,
        on_delete=models.SET_NULL,  # Actor is just the last commenter
    )
    last_comment = models.ForeignKey(
        'DiaryComment',
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # Deleting a comment doesn't affect the diary
    )
    reply_count = models.PositiveIntegerField(default=0)
    sticky = models.BooleanField(default=False)
    is_pyggy = models.BooleanField(default=False)

    objects = DiaryEntryManager()
    activity_log_events = EventRelation()

    class Meta:
        get_latest_by = 'activity'
        ordering = ['-created', 'title']
        verbose_name_plural = "DiaryEntries"

    def __repr__(self):
        return f'{self.title!r} by {self.user!r}'
    def __str__(self):
        return f'{self.title} by {self.user}'

    def summary(self):
        ''' summary text - remove HTML and truncate '''
        text = html2text(self.content)
        if len(text) > 255:
            text = text[:252] + '...'
        return text

    def get_absolute_url(self):
        return reverse("display-diary", args=[self.id])


class DiaryComment(models.Model):
    challenge = models.ForeignKey(
        Challenge,
        blank=True,
        null=True,
        on_delete=models.SET_NULL,  # many redundant relationships here
    )
    diary_entry = models.ForeignKey(
        DiaryEntry,
        on_delete=models.CASCADE,  # nowhere to show a comment if diary is gone
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # deleting a user should delete their activity
    )
    content = models.TextField()
    created = models.DateTimeField(default=now)
    edited = models.DateTimeField(null=True)

    class Meta:
        get_latest_by = 'created'
        ordering = ['created']

    def __repr__(self):
        return f'diary_comment-{self.id!r}'
    __str__ = __repr__


def file_upload_location(instance, filename):
    return os.path.join(str(instance.challenge.number), str(instance.entry.name), filename)


class File(models.Model):
    challenge = models.ForeignKey(
        Challenge,
        null=True,
        on_delete=models.SET_NULL,  # Challenge doesn't own the file
    )
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,  # Entries own their files
    )
    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,  # Files uploaded by one team member on behalf
                                    # of the whole team must not be deleted if
                                    # that user is deleted
    )
    thumb_width = models.PositiveIntegerField(default=0)
    content = models.FileField(upload_to=file_upload_location)
    created = models.DateTimeField(default=now)
    description = models.CharField(max_length=255)
    is_final = models.BooleanField(default=False)
    is_screenshot = models.BooleanField(default=False)

    activity_log_events = EventRelation()

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']

    def get_image_role(self):
        """Return a string indicating the role of the image.

        * screenshot - if the image looks like a screenshot
        * graphic - if the image looks like a smaller graphic
        * animation - if the image contains multiple frames

        """
        from PIL import Image
        try:
            im = Image.open(self.content)
            width, height = im.size
            try:
                im.seek(1)
            except EOFError:
                pass
            else:
                return 'animation'
            return 'screenshot' if width * height > 3e5 else 'graphic'
        except Exception:
            import traceback
            traceback.print_exc()
            return 'screenshot'

    def __repr__(self):
       return f'file for {self.entry!r} ({self.description!r})'
    def __str__(self):
       return f'file for {self.entry} ({self.description})'

    def filename(self):
        return os.path.basename(self.content.name)

    def pretty_size(self):
        size = self.content.size
        unitSize= {'': 1, 'K': 1024.0, 'M': 1048576.0, 'G': 1073741824.0}
        if size < 1024:
            unit = ''
        elif size < 1048576:
            unit = 'K'
        elif size < 1073741824:
            unit = 'M'
        else:
            unit = 'G'
        sizeInUnit = size/unitSize[unit]
        return f'{sizeInUnit:0.2f} {unit}bytes'


def award_upload_location(instance, filename):
    return os.path.join('awards', str(instance.creator.id), filename)


class Award(models.Model):
    creator = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,  # awards belong to their recipients
    )
    created = models.DateTimeField(default=now)
    content = models.FileField(upload_to=award_upload_location)
    description = models.CharField(max_length=255)

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']

    def __repr__(self):
        return f'award from {self.creator!r} ({self.description!r})'
    def __str__(self):
        return f'award from {self.creator} ({self.description})'

    def filename(self):
        return os.path.basename(self.get_content_filename())


class EntryAward(models.Model):
    creator = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,  # awards belong to their recipients
    )
    created = models.DateTimeField(default=now)
    challenge = models.ForeignKey(
        Challenge,
        null=True,
        on_delete=models.SET_NULL,  # awards belong to entries not challenges
    )
    entry = models.ForeignKey(
        Entry,
        on_delete=models.CASCADE,  # deleting an entry deletes the awards it has received
    )
    award = models.ForeignKey(
        Award,
        on_delete=models.CASCADE,  # if an award must be deleted it is deleted from all entries
    )

    activity_log_events = EventRelation()

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']


    def __repr__(self):
        return f'{self.award!r} to {self.entry!r}'
    def __str__(self):
        return f'{self.award} to {self.entry}'

    def content(self):
        return self.award.content

    def description(self):
        return self.award.description


BEST_TEN = 0
SELECT_MANY = 1
INSTANT_RUNOFF = 2
POLL = 3
STAR_VOTE = 4
POLL_CHOICES = (
    (BEST_TEN, 'Ten Single Votes'),
    (SELECT_MANY, 'Select Many'),
    (INSTANT_RUNOFF, 'Instant-Runoff'),
    (POLL, 'Poll'),
    (STAR_VOTE, 'STAR Voting'),
)
class Poll(models.Model):
    challenge = models.ForeignKey(
        Challenge,
        on_delete=models.CASCADE,  # Theme polls are owned by a challenge
    )
    title = models.CharField(max_length=100)
    description = models.TextField()
    created = models.DateTimeField(default=now)
    is_open = models.BooleanField()
    is_hidden = models.BooleanField()
    is_ongoing = models.BooleanField()
    type = models.IntegerField(
        choices=POLL_CHOICES,
        help_text="STAR Voting is the type for challenge theme polls.",
        default=STAR_VOTE
    )

    BEST_TEN=BEST_TEN
    SELECT_MANY=SELECT_MANY
    INSTANT_RUNOFF=INSTANT_RUNOFF
    POLL=POLL
    STAR_VOTE=STAR_VOTE
    POLL_CHOICES=POLL_CHOICES

    class Meta:
        get_latest_by = 'created'
        ordering = ['-created']

    def __str__(self):
        if self.challenge:
            return f'<Poll {self.title} challenge {self.challenge}>'
        else:
            return f'<Poll {self.title}>'


class Option(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,  # Options are owned by a poll
    )
    text = models.CharField(max_length=100)

    class Meta:
        ordering = ['id']
        unique_together = (("poll", "text"),)

    def __str__(self):
        return f'Poll {self.poll} Option "{self.text}"'

    __repr__ = __str__


class Response(models.Model):
    poll = models.ForeignKey(
        Poll,
        on_delete=models.CASCADE,  # Responses are owned by a poll
    )
    option = models.ForeignKey(
        Option,
        on_delete=models.RESTRICT,  # Shouldn't delete options independently
                                    # of deleting the whole poll
    )
    user = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,  # Once entered a poll response should not
                                    # be deleted if the user is deleted
    )
    created = models.DateTimeField(default=now)
    value = models.IntegerField()

    class Meta:
        get_latest_by = 'created'
        unique_together = (("option", "user"),)

    def __repr__(self):
        if self.value:
            return f'{self.user!r} chose {self.option!r} ({self.value!r})'
        else:
            return f'{self.user!r} chose {self.option!r}'
    __str__ = __repr__


class UserProfile(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,  # Profiles are owned by a user
    )
    twitter_username = models.CharField(
        max_length=15,
        blank=True,
        null=True,
        unique=True,
        help_text="The username of your Twitter account.",
    )
    github_username = models.CharField(
        max_length=39,
        blank=True,
        null=True,
        unique=True,
        help_text="The username of your GitHub account.",
    )
    content = models.TextField(blank=True)
