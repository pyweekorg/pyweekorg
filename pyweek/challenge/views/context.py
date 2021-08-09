from pyweek.challenge.models import Challenge, Entry


def challenges(request):
    latest, previous = Challenge.objects.get_latest_and_previous()

    # challenge is the nearest challenge: the one just gone, unless there's
    # a new one which is running or open for registration
    challenge = latest if latest and not latest.isCompComing() else previous

    unverified_emails = 0
    if not request.user.is_anonymous:
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
