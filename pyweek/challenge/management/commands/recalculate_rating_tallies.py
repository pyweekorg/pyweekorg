from __future__ import print_function

from django.db.models import Q
from django.core.management.base import BaseCommand, CommandError

from pyweek.challenge.models import Challenge



class Command(BaseCommand):
    def add_arguments(self, parser):
        # Named (optional) arguments
        parser.add_argument(
            'challenge',
            help='The challenge we are fixing.'
        )

    def handle(self, *args, **options):
        challenge_id = options['challenge']
        challenge = Challenge.objects.get(pk=challenge_id)

        all_done = challenge.isAllDone()
        if not all_done:
            raise CommandError('Challenge is not finished!')

        challenge.generate_tallies()
        print("Updated rating tallies for PyWeek {}".format(challenge_id))
        print("Individual winners reset to:")
        for e in challenge.individualWinners():
            title = e.game or e.title
            print(' ', title)
        print()
        print("Team winners reset to:")
        for e in challenge.teamWinners():
            title = e.game or e.title
            print(' ', title)

