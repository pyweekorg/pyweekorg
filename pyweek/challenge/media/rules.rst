----------------------------------------
PyWeek Game Progamming Challenge Rules
----------------------------------------

:revision date: 2010/04/08


The PyWeek challenge:

1. Must be challenging and fun,
2. Entries must be developed during the challenge, and must
   incorporate some theme decided at the start of the challenge,
3. Will hopefully increase the public body of python game tools, code
   and expertise,
4. Will let a lot of people actually finish a game, and
5. May inspire new projects (with ready made teams!)

.. contents::


1. Entry is individual or team-based
------------------------------------

You may either enter as an individual or as a team with as many members as
you like. Individuals and teams will be judged together (we figure the benefits
of being in a team are outweighed by the disadvantages of being in a team).

All members of a team get to vote (though not for their own team), enter diary
entries and upload files. People may join more than one team.

During the challenge, competitors are encouraged to hang out on IRC and
post diary entries (diaries are supplied as part of the challenge).

By signing up to the challenge, you are agreeing to abide by
the system `conditions of use`__.

__ conditions.html


2. Entries are to be written "from scratch"
-------------------------------------------

The intent of this rule is to provide a level playing-field for all entrants. This has
a number of aspects:

1. You can't have a personal "library" codebase that you use during
   the competition,
2. If you do have a library you must release it within a reasonable
   amount of time (at least 1 month) before the challenge starts so
   that others may have reasonable opportunity of using the library, and
3. If you do release a new version of a library around the time of the
   challenge, we would ask that you make all efforts to not sabotage
   existing users of your library (see rule `9. Target Platform`_.)
   It's probably safer to wait until after the competition to release
   the new version, and use the old version for the competition.

You are allowed to use existing libraries that have been available
for at least one month before the challenge (and are well documented).
The libraries must not implement any game logic. The entire PyGame library
is OK to use, as are PIL, PyOpenGL, PyODE, PyOGRE, etc -- all the libraries
listed in the `python.org PythonGameLibraries wiki page`__.

.. __: http://wiki.python.org/moin/PythonGameLibraries

You are **not** allowed to use any **exising personal codebases**. This
includes using those codebases as a point of reference. Hint: release the
code well before the comp as part of a tutorial. Then you may refer to
it -- and so may the other competitors.

A great resource is the `pygame.org cookbook`__. It is perfectly
acceptable to cut-n-paste code from the cookbook, as that code is released
and should be considered equivalent to a library.

.. __: http://www.pygame.org/wiki/CookBook

This is a Python programming challenge, but that doesn't preclude the use
of supporting languages (eg. C or C++ libraries, Javascript in HTML web
pages, and so on).


3. The time limit is 1 week
---------------------------

The challenge starts 00:00 UTC Sunday and finishes 7 days later at
00:00UTC Sunday.

Work done on entries before this time would be considered cheating.

Once the time limit is up entrants will have 24 hours to upload their
file(s). This is not extra development time. Failure to upload at the
last minute of that additional 24 hours will be met with zero leniency.
The server will overload if you try. You have been warned.

If your game crashes it's on your head. You should allow time for
testing well before the deadline.


4. Theme is selected by the competitors
---------------------------------------

The theme of the challenge will be determined by a vote in the
week leading up to the challenge.

The theme exists to serve two purposes:

1. Inspire entrants at the start of the challenge, and
2. Discourage cheating.

How entrants interpret the theme (whether it be cosmetically or for deeper
meaning) is completely open.

A person known to the PyWeek organisers, but otherwise independent
and *not* a participant, will create a list of five themes.

In the week leading up to the challenge, all participants get to place a
preference against each of the five themes. The vote preferences are tallied,
according to instant-runoff rules. The winner of that vote is announced
at the point that the challenge begins.

All votes will be recorded for later examination.


5. Entries are judged by peers
------------------------------

Judging of final submissions will be done by your peers, the other souls brave
enough to grind away for 7 days and compete with you (and finish).
Judging is performed by the
individual competitors, so every member of a team entry gets to vote.
Competitors are not allowed to vote for any submissions they are involved with (so
people signed up to multiple teams can vote for none of those teams).

Judging will be done in three categories rated 1-5:

- Fun
- Innovation
- Production (graphics, sound, polish)
- Overall

Gold, silver and bronze awards will be given for each category.

If the game did not work for a judge, they may mark the game "Did Not Work".
Their ratings in the categories above will not count towards its final
ratings tally.

Finally, competitors may vote that a submission be disqualified for one of three
reasons:

- Did not follow the theme of the challenge,
- Did not work on the target platform, or
- Entrant cheated.

A submission that gets more than 50% disqualification votes is not eligible
for any prizes, though they'll still appear in the rankings ("do'h, if
only I'd followed the rules!")


6. Existing artwork, music and sound effects may be used
--------------------------------------------------------

As with the use of existing codebases, the intention is that all entrants
start with a level playing field in artwork too. This means you shouldn't
develop artwork beforehand that you intend to use during the challenge
*unless* you also make that artwork freely available to all other entrants.

There should be absolutely no breach of licensing. You can't just
cut-n-paste in artwork from The Simpsons (TM).

First suggestion, try a web search for "free fonts" or "free clip-art" etc.

A list of good, free art resources go to the PyGame website wiki (and
contribute!) at http://www.pygame.org/wiki/resources


7. Your Final Submission
------------------------

You may upload your final at any time during the challenge. You may even
upload multiple final submissions - but only the last one will actually be
used for judging.

Your entry **must** include all code and data required for running, and
instructions about how to run the entry. Consider using py2exe to generate
a Windows executable (though also recognise that some people don't have
Windows.) It is recommended that you include 3rd-party libraries if
that's reasonable (ie. if they're pure-Python and don't bloat out your
entry size unreasonably).

We recommend you download the `Skellington 1.9`__ package and use that as the starting-point
for your game.

__ http://media.pyweek.org/static/skellington-1.9.zip

Your entry **must** include all source code. You retain ownership of all source
code and artwork you produce. The Free Software Foundation has a handy
`page of free software licenses`__ which may help you figure out how to
license your entry.

__ http://www.fsf.org/licensing/licenses

Your game's license must allow for PyWeek to redistribute your
game and its source through the PyWeek website (http://pyweek.org/),
BitTorrent and any other protocol deemed necessary by the PyWeek
organisers.

Please read the `entrant help page`__ for some guidelines about how to
package your entry.

__ http://media.pyweek.org/static/help.html


8. Allowed Documentation
------------------------

Any online documentation may be used. This encompasses anything that might
be viewed in a web browser and found by Google by any of the challenge
entrants. Mailing lists and bulletin boards count. 

If online documentation includes code snippets, that's ok, just don't
cut-n-paste the code directly into your game. 

If the online documentation is only code (ie. it's a web CVS viewer, or
similar) then it's not OK. 

Any existing code you've written should be considered out-of-bounds for the
duration of the challenge.


9. Target platform
------------------

All entries must run in Python on the latest available libraries (ie. the latest
release of PyGame, PyOpenGL, etc).

This doesn't mean you have to develop on those latest versions, just that
any code you produce must work on those versions.

If you are the maintainer of a library, we would ask that you make all efforts to not
sabotage existing users of your library. It's probably safer to wait until after the
challenge to release the new version, and use the old version for the challenge.

-------------------


The `PyWeek Game Programming Challenge`__ Rules Committee <pyweek1@mechanicalcat.net>

__ http://www.mechanicalcat.net/tech/PyWeek
