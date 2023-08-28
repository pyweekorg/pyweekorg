import itertools
from operator import itemgetter
from typing import Callable
from collections import Counter, defaultdict

import starvote

from .models import Poll


def responses_by_user(poll: Poll) -> list[dict[str, int]]:
    """Get all responses to a poll, grouped by user."""
    option_names = {
        option.id: option.text
        for option in poll.option_set.all()
    }
    by_user = defaultdict(dict)
    for vote in poll.response_set.all():
        name = option_names[vote.option_id]
        by_user[vote.user_id][name] = vote.value
    return list(by_user.values())


def acceptance_vote(
    options: list[str],
    responses: list[dict[str, int]],
    print: Callable = print
) -> str:
    """Tally ratings where users can vote once for one or more candidates."""
    tally = Counter(dict.fromkeys(options, 0))
    tally.update(
        option
         for user_votes in responses
         for option, value in user_votes.items()
         if value > 0
    )
    scores = tally.most_common()
    for name, count in scores:
        print(f"{name}: {count} votes")
    print()

    winner = scores[0][0]
    print(f"Winner: {winner}!")
    return winner


def instant_runoff(
    options: list[str],
    responses: list[dict[str, int]],
    print: Callable = print,
) -> str:
    """Take the votes as recorded, and figure a majority winner
    according to instant-runoff rules.

    First choices are tallied. If no candidate has the support of a
    majority of voters, the candidate with the least support is
    eliminated. A second round of counting takes place, with the votes
    of supporters of the eliminated candidate now counting for their
    second choice candidate. After a candidate is eliminated, he or she
    may not receive any more votes.

    This process of counting and eliminating is repeated until one
    candidate has over half the votes. This is equivalent to continuing
    until there is only one candidate left.
    """
    num_voters = len(responses)
    in_running = options.copy()
    for round_num in itertools.count(start=1):
        tally = Counter({candidate: 0 for candidate in in_running})
        tally.update(
            min(in_running, key=response.__getitem__)
            for response in responses
        )

        print(f"[Round {round_num}]")

        # Very important: ties are broken by ordering in the list of options,
        # and that order is *this*. We rely on stable sorting and then we
        # reverse it.
        #
        # This happened in PyWeek 31, for example - after round 2 there was a
        # 4-way tie.
        scores = sorted(tally.items(), key=itemgetter(1))[::-1]
        for choice, count in scores:
            percent = round(100.0 * count / num_voters)
            print(f"{percent}% {choice}")
        print()

        leader, leader_score = scores[0]
        if leader_score > num_voters / 2.:
            percent = round(100.0 * leader_score / num_voters)
            print(f"{leader} has {percent}% of the vote and is the winner!")
            return leader
        else:
            print("No candidate has >50% of the vote.")

            eliminated = scores[-1][0]
            print(f"Trailing candidate {eliminated} has been eliminated.")
            print()
            in_running = [c for c in in_running if c != eliminated]


def star_vote(
    options: list[str],
    responses: list[dict[str, int]],
    print: Callable = print,
):
    winners = starvote.election(
        starvote.STAR_Voting,
        responses,
        seats=1,
        verbosity=1,
        print=print,
    )
    # starvote supports elections with more than one winner, but we will only
    # have one.
    return winners[0]



TALLY_FUNCTIONS = {
    Poll.BEST_TEN: acceptance_vote,
    Poll.SELECT_MANY: acceptance_vote,
    Poll.INSTANT_RUNOFF: instant_runoff,
    Poll.POLL: acceptance_vote,
    Poll.STAR_VOTE: star_vote,
}


def tally(poll: Poll, print: Callable = print) -> str:
    """Tally voting for the given poll."""
    options = [option.text for option in poll.option_set.all()]
    responses = responses_by_user(poll)
    return TALLY_FUNCTIONS[poll.type](options, responses, print=print)
