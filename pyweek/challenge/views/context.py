from pyweek.challenge.models import Challenge, Entry


def challenges(request):
    latest, previous = Challenge.objects.get_latest_and_previous()

    if not request.user.is_anonymous():
        entries = Entry.objects.filter(
            challenge__number__lt=1000,
            users__username__exact=request.user.username)
    else:
        entries = []
    return {'all': all, 'previous': previous, 'latest': latest, 'challenge': latest, 'user_entries': entries}
