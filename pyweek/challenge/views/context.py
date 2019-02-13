from pyweek.challenge.models import Challenge, Entry


def challenges(request):
    latest, previous = Challenge.objects.get_latest_and_previous()

    challenge = latest if latest.isRegoOpen() else previous

    unverified_emails = 0
    if not request.user.is_anonymous():
        latest_entries = request.user.entry_set.filter(challenge=challenge)
        unverified_emails = (
            request.user.emailaddress_set
            .filter(verified=False)
            .count()
        )
    else:
        latest_entries = Entry.objects.none()

    return {
        'all': all,
        'previous': previous,
        'latest': latest,
        'challenge': latest,
        'user_entries': latest_entries,
        'unverified_emails': unverified_emails,
    }
