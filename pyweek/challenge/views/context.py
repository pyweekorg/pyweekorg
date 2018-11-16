from pyweek.challenge.models import Challenge, Entry


def challenges(request):
    latest, previous = Challenge.objects.get_latest_and_previous()

    challenge = latest if latest.isRegoOpen() else previous

    if not request.user.is_anonymous():
        latest_entries = request.user.entry_set.filter(challenge=challenge)
    else:
        latest_entries = Entry.objects.none()

    return {
        'all': all,
        'previous': previous,
        'latest': latest,
        'challenge': latest,
        'user_entries': latest_entries,
    }
