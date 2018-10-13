"""Log Github commits to the activity log."""
import requests
import datetime
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings

from pyweek.challenge.models import Entry, Challenge, User
from pyweek.activity.models import log_event

session = requests.session()


class Command(BaseCommand):
    help = 'Check for Github pushes for Pyweek entries.'

    def handle(self, *args, **options):
        challenge = Challenge.objects.latest()
        if not challenge.isCompRunning():
            return

        entries = challenge.challenge.filter(github_repo__isnull=False)

        self.github_token = getattr(settings, 'GITHUB_TOKEN', None)

        # We'll do 1/3 of the entries every 10 minutes
        # thus all entries twice per hour
        partition = (datetime.datetime.now().minute // 10) % 3

        for e in entries:
            epartition = hash(e.name) % 3
            if epartition != partition:
                continue
            try:
                self.query_github(e)
            except Exception:
                import traceback
                traceback.print_exc()

    def query_github(self, entry):
        repo = entry.github_repo
        url = 'https://api.github.com/repos/{}/commits'.format(repo)
        headers = {}
        if self.github_token:
            headers['Authorization'] = 'token {}'.format(self.github_token)
        resp = requests.get(url, headers=headers)
        if resp.status_code != 200:
            self.stdout.write(
                "Error {} polling {}".format(
                    resp.status_code,
                    url
                )
            )
            return

        resp_json = resp.json()
        if not resp_json:
            return

        users = set()
        commits = []

        for commit in resp.json():
            sha = commit['sha']
            if sha == entry.head_sha:
                break

            msg = commit['commit']['message'].splitlines()[0]
            users.add(commit['committer']['login'])
            commits.append({
                'msg': msg,
                'sha': sha,
            })

        if not commits:
            return

        users = User.objects.filter(userprofile__github_username__in=users)

        entry.head_sha = commits[0]['sha']
        log_event(
            type="github-push",
            repo=entry.github_repo,
            users=[u.username for u in users],
            commits=commits,
            game=entry.display_title,
            name=entry.name,
        )
        entry.save()


