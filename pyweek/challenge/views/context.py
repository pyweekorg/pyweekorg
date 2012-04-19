
def challenges(request):
    from pyweek.challenge.models import Challenge, Entry
    all = list(Challenge.objects.filter(number__lt=1000))
    latest = previous = None
    if all:
        latest = all[-1]
        if len(all) > 1:
            previous = all[-2]
    if not request.user.is_anonymous():
        entries = Entry.objects.filter(
            challenge__number__lt=1000,
            users__username__exact=request.user.username)
    else:
        entries = []
    return {'all': all, 'previous': previous, 'latest': latest, 'challenge': latest, 'user_entries': entries}
