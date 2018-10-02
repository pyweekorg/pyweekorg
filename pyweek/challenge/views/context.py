from pyweek.challenge.models import Challenge, Entry


def challenges(request):
    latest, previous = Challenge.objects.get_latest_and_previous()

    if not request.user.is_anonymous():
        latest_entries = request.user.entry_set.filter(challenge=latest)
    else:
        latest_entries = Entry.objects.none()

    return {
        'all': all,
        'previous': previous,
        'latest': latest,
        'challenge': latest,
        'user_entries': latest_entries,
    }
