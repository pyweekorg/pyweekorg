from functools import partial
import html
from io import StringIO

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponse
from django.contrib import messages
from pyweek.challenge.models import Poll, Response, Option

from .. import theme_voting


instructions = {
    Poll.BEST_TEN: 'Select your ten preferred items from the list.',
    Poll.SELECT_MANY: 'Select your preferred items from the list.',
    Poll.INSTANT_RUNOFF: '''Place a number against each option, numbered 1
    (for your most preferred choice) through %(num_choices)s (for your
    least preferred choice).''',
    Poll.POLL: 'Select your preferred item from the list.',

    Poll.STAR_VOTE: (
        "Please enter a score from 0 to 5 for each option, where 5 is "
        "highly preferred and 0 is highly disliked."
    ),
}


def poll_display(request, poll_id):
    """Display a poll."""
    poll = get_object_or_404(Poll, pk=poll_id, is_hidden=False)
    info = {
        'num_choices': len(poll.option_set.all()),
    }
    return render(request, 'challenge/poll.html', {
        'poll': poll,
        'instructions': instructions[poll.type]%info,
        'challenge': poll.challenge,
        'fields': render_poll(poll, request)
    })


def poll_view(request, poll_id):
    poll = get_object_or_404(Poll, pk=poll_id)
    ok = False
    if request.user.is_superuser:
        ok = True
    elif poll.is_hidden or not poll.is_open:
        ok = False
    elif not poll.is_ongoing:
        ok = True
    if not ok:
        return HttpResponse('not allowed')
    info = {
        'num_choices': len(poll.option_set.all()),
    }
    return render(request, 'challenge/poll.html', {
        'poll': poll,
        'instructions': instructions[poll.type]%info,
        'challenge': poll.challenge,
        'fields': render_poll(poll, request, force_display=True)
    })


def render_poll(poll, request, force_display=False):
    if poll.is_open and not force_display:
        if request.user.is_anonymous:
            return '<p>You must log in to vote.</p>'
        return render_fields(poll, request)
    else:
        output = StringIO()
        buffered_print = partial(print, file=output)
        respondents = poll.response_set.count()

        if not poll.is_open:
            buffered_print("Polling is closed.")
            buffered_print(f"There were {respondents} respondents.\n")

        _winner = theme_voting.tally(poll, print=buffered_print)

        return (
            ('<a href="..">(Re)cast your votes</a>\n' if poll.is_ongoing else '')
            + '<div style="white-space: pre-line">'
            + html.escape(output.getvalue())
            + '</div>'
        )


def render_fields(poll, request):
    '''Figure the votes display for the current user.'''
    l = poll.response_set.filter(user__pk=request.user.id)
    votes = {vote.option_id: vote.value for vote in l}

    message = ''
    if request.POST:
        votes, errors = handle_votes(poll, votes, request)
        if errors:
            message = '<br />'.join(errors)
        else:
            for response in l:
                response.delete()
            for choice, value in list(votes.items()):
                option = Option.objects.get(pk=choice)
                r = Response(option=option, value=value,
                    user=request.user, poll=poll)
                r.save()
            messages.success(request, 'Vote recorded')

    l = []
    if message:
        l.append(f'<div class="form-error">{message}</div>')
    if votes and poll.type in (Poll.BEST_TEN, Poll.SELECT_MANY):
        l.append(f'<p>You have selected {len(votes)} choices.</p>')
    l.append('<form method="POST" action="."><table>')
    choices = list(poll.option_set.all())
    if poll.is_ongoing:
        choices.sort(key=lambda o: o.text)
    for choice in choices:
        l.append('<tr><td>%s</td><td>%s</td></tr>'%(
            choice_field(poll, choice.id, votes), html.escape(choice.text)))
    l.append('<tr><td>&nbsp;</td><td><input type="submit"></td></tr>')
    l.append('</table></form>')
    return '\n'.join(l)


def choice_field(poll, choice, votes):
    ' render one choice field, based on the method '
    if poll.type in (Poll.BEST_TEN, Poll.SELECT_MANY):
        checked = choice in votes and ' checked' or ''
        return f'<input name="votes" type="checkbox" value="{choice}"{checked}>'
    elif poll.type == Poll.POLL:
        checked = choice in votes and ' checked' or ''
        return f'<input name="vote" type="radio" value="{choice}"{checked}>'
    elif poll.type in (Poll.INSTANT_RUNOFF, Poll.STAR_VOTE):
        value = votes.get(choice, '')
        return f'<input name="vote-{int(choice)}" size="2" value="{value}">'
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
        have = set()
        options = poll.option_set.all()
        for option in options:
            key = f'vote-{option.id}'
            if key not in request.POST:
                errors.append("Must place a number against all choices")
            try:
                v = int(request.POST[key])
            except ValueError:
                errors.append("Votes must be numbers")
                continue
            if v <= 0:
                errors.append("Votes must be numbers > 0")
            n = len(options)
            if v > n:
                errors.append(f"Votes must be numbers <= {n}")
            if v in have:
                errors.append(f"Can't vote {int(v)} twice")
            d[option.id] = v
            have.add(v)
    elif poll.type == Poll.STAR_VOTE:
        d = {}
        for option in poll.option_set.all():
            try:
                v = int(request.POST[f'vote-{option.id}'])
            except KeyError:
                errors.append("Must place a score against all choices")
            except ValueError:
                errors.append("Scores must be numbers")
                continue

            if not (0 <= v <= 5):
                errors.append("Scores must be between 0 and 5 (inclusive)")
            d[option.id] = v
    return d, list(set(errors))


def render_tally(poll, tally):
    # Render the results of voting
    l = ['<table>']
    tally = [(Option.objects.get(pk=choice_value[0]), choice_value[1]) for choice_value in list(tally.items())]
    if poll.is_ongoing:
        tally.sort(key=lambda o: o[0].text)
    else:
        tally.sort(key=lambda o: o[1], reverse=True)
    n = 0
    for choice, value in tally:
        choice = html.escape(str(choice.text))
        if poll.type == Poll.INSTANT_RUNOFF:
            l.append(f'<tr><td>{int(value)}%</td><td>{choice}</td></tr>')
        else:
            if poll.type == Poll.POLL and n == 0:
                choice = f'<b>{choice}</b>'
            elif poll.type == Poll.BEST_TEN and n < 10:
                choice = f'<b>{choice}</b>'
            l.append(f'<tr><td>{int(value)}</td><td>{choice}</td></tr>')
        n += 1
    l.append('</table>')
    #l.append('<!-- %d respondents -->'%len(self.votes))
    return '\n'.join(l)

