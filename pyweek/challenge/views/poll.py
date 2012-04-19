import cgi
import sets

from django.shortcuts import render_to_response, get_object_or_404
from django.template import RequestContext
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from pyweek.challenge.models import Poll, Response, Option
from django import forms

instructions = {
    Poll.BEST_TEN: 'Select your ten preferred items from the list.',
    Poll.SELECT_MANY: 'Select your preferred items from the list.',
    Poll.INSTANT_RUNOFF: '''Place a number against each option, numbered 1
    (for your most preferred choice) through %(num_choices)s (for your
    least preferred choice).''',
    Poll.POLL: 'Select your preferred item from the list.',
}

def poll_display(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    info = {
        'num_choices': len(poll.option_set.all()),
    }
    return render_to_response('challenge/poll.html', {'poll': poll,
        'instructions': instructions[poll.type]%info,
        'challenge': poll.challenge, 'fields': render(poll, request)},
        RequestContext(request))

def poll_view(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    if not (poll.is_ongoing or (not request.user.is_anonymous() and request.user.is_superuser)):
        return HttpResponse('not allowed')
    info = {
        'num_choices': len(poll.option_set.all()),
    }
    return render_to_response('challenge/poll.html', {'poll': poll,
        'instructions': instructions[poll.type]%info,
        'challenge': poll.challenge, 'fields': render(poll, request,
        force_display=True)}, RequestContext(request))

def render(poll, request, force_display=False):
    if poll.is_open and not force_display:
        if request.user.is_anonymous():
            return '<p>You must log in to vote.</p>'
        return render_fields(poll, request)
    else:
        s = ''
        if not poll.is_open:
            s += '<p>Polling is closed.</p>'
        elif poll.is_ongoing:
            s += '<p><a href="..">(Re)cast your votes</a></p>'
        num, tally = poll.tally()
        s += render_tally(poll, tally)

        if poll.type == Poll.INSTANT_RUNOFF:
            s += '<p>After preferences:</p>'
            num, tally = poll.instant_runoff()
            s += render_tally(poll, tally)

        s += '<p>There were %d respondents.</p>'%num
        return s

class PollManipulator(forms.Manipulator):
    def __init__(self, poll):
        choices = [(option.id, option.text)
            for option in poll.option_set.all()]
        self.fields = (
            formfields.RadioSelectField(field_name='choice',
                choices=choices, is_required=True),
        )

def render_fields(poll, request):
    '''Figure the votes display for the current user.'''
    l = poll.response_set.filter(user__pk=request.user.id)
    votes = dict([(vote.option_id, vote.value) for vote in l])

    message = ''
    if request.POST:
        votes, errors = handle_votes(poll, votes, request)
        if errors:
            message = '<br />'.join(errors)
        else:
            for response in l:
                response.delete()
            for choice, value in votes.items():
                option = Option.objects.get(pk=choice)
                r = Response(option=option, value=value,
                    user=request.user, poll=poll)
                r.save()
            if poll.is_ongoing:
                request.user.message_set.create(message='Vote recorded. ' +
                    '<a href="view">View current results</a>.')
            else:
                request.user.message_set.create(message='Vote recorded')

    l = []
    if message:
        l.append('<div class="form-error">%s</div>'%message)
    if votes and poll.type in (Poll.BEST_TEN, Poll.SELECT_MANY):
        l.append('<p>You have selected %s choices.</p>'%len(votes))
    l.append('<form method="POST" action="."><table>')
    choices = list(poll.option_set.all())
    if poll.is_ongoing:
        choices.sort(lambda a,b: cmp(a.text, b.text))
    for choice in choices:
        l.append('<tr><td>%s</td><td>%s</td></tr>'%(
            choice_field(poll, choice.id, votes), cgi.escape(choice.text)))
    l.append('<tr><td>&nbsp;</td><td><input type="submit"></td></tr>')
    l.append('</table></form>')
    return '\n'.join(l)


def choice_field(poll, choice, votes):
    ' render one choice field, based on the method '
    if poll.type in (Poll.BEST_TEN, Poll.SELECT_MANY):
        checked = votes.has_key(choice) and ' checked' or ''
        return '<input name="votes" type="checkbox" value="%s"%s>'%(
            choice, checked)
    elif poll.type == Poll.POLL:
        checked = votes.has_key(choice) and ' checked' or ''
        return '<input name="vote" type="radio" value="%s"%s>'%(choice, checked)
    elif poll.type == Poll.INSTANT_RUNOFF:
        value = votes.get(choice, '')
        return '<input name="vote-%d" size="2" value="%s">'%(choice, value)
    else:
        return 'oops'


def handle_votes(poll, current, request):
    '''Snarf votes from the form.
    '''
    errors = []
    if poll.type == Poll.POLL:
        d = {int(request.POST['vote']): 1}
    elif poll.type in (Poll.BEST_TEN, Poll.SELECT_MANY):
        l = request.POST.getlist('votes')
        if not isinstance(l, type([])):
            l = [l]
        if poll.type == Poll.BEST_TEN and len(l) > 10:
            errors.append( "Can't vote for more than ten choices.")
        d = {}
        for item in l:
            d[int(item)] = 1
    elif poll.type == Poll.INSTANT_RUNOFF:
        d = {}
        have = {}
        options = poll.option_set.all()
        for option in options:
            key = 'vote-%s'%option.id
            if not request.POST.has_key(key):
                errors.append( "Must place a number against all choices")
            try:
                v = int(request.POST[key])
            except ValueError:
                errors.append( "Votes must be numbers")
            if v <= 0:
                errors.append( "Votes must be numbers > 0")
            n = len(options)
            if v > n:
                errors.append( "Votes must be numbers <= %s"%n)
            if have.has_key(v):
                errors.append( "Can't vote %d twice"%v)
            d[option.id] = v
            have[v] = True
    return d, list(sets.Set(errors))

def render_tally(poll, tally):
    # Render the results of voting
    l = ['<table>']
    tally = map(lambda (choice, value): 
                 (Option.objects.get(pk=choice), value), tally.items())
    if poll.is_ongoing:
        tally.sort(lambda a,b:cmp(a[0].text, b[0].text))
    else:
        tally.sort(lambda a,b:cmp(a[1],b[1]))
        tally.reverse()
    n = 0
    for choice, value in tally:
        choice = cgi.escape(str(choice.text))
        if poll.type == Poll.INSTANT_RUNOFF:
            l.append('<tr><td>%d%%</td><td>%s</td></tr>'%(value, choice))
        else:
            if poll.type == Poll.POLL and n == 0:
                choice = '<b>%s</b>'%choice
            elif poll.type == Poll.BEST_TEN and n < 10:
                choice = '<b>%s</b>'%choice
            l.append('<tr><td>%d</td><td>%s</td></tr>'%(value, choice))
        n += 1
    l.append('</table>')
    #l.append('<!-- %d respondents -->'%len(self.votes))
    return '\n'.join(l)

