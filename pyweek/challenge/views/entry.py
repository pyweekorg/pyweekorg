import urllib.request
import urllib.parse
import urllib.error
import random
import hashlib
import operator

from django import forms
from django.db import models as md
from django.contrib import messages
from django.shortcuts import render, get_object_or_404
from django.template import RequestContext
from django.http import (
    HttpResponse, HttpResponseRedirect, HttpResponseForbidden
)
from pyweek.challenge import models
from pyweek import settings
from django.core import validators
from django.contrib.auth.decorators import login_required

from pyweek.bleaching import html2text, html2safehtml
from pyweek.activity.models import log_event
from pyweek.activity.summary import summarise
from pyweek.mail import sending
from pyweek.users.models import EmailAddress


safeTags = '''b a i br blockquote table tr td img pre p dl dd dt
    ul ol li span div'''.split()


GITHUB_REGEX = (
    r'^[A-Za-z\d](?:[A-Za-z\d]|-(?=[A-Za-z\d])){0,38}/'
    r'[A-Za-z\d](?:[A-Za-z\d]|-(?=[A-Za-z\d])){0,38}$'
)


def isUnusedEntryName(field_data: str) -> None:
    if models.Entry.objects.filter(name__exact=field_data):
        raise validators.ValidationError(f'"{field_data}" already taken')


def isUnusedEntryTitle(field_data: str) -> None:
    if models.Entry.objects.filter(title__exact=field_data):
        raise validators.ValidationError(f'"{field_data}" already taken')


def isCommaSeparatedUserList(field_data: str) -> None:
    for name in [e.strip() for e in field_data.split(',')]:
        if not models.User.objects.filter(username__exact=name):
            raise validators.ValidationError(f'No such user {name}')


class BaseEntryForm(forms.ModelForm):
    title = forms.CharField(
        required=True,
        label="Team name",
        widget=forms.TextInput(attrs={
            'size': '50',
        })
    )
    github_repo = forms.RegexField(
        regex=GITHUB_REGEX,
        required=False,
        empty_value=None,
        widget=forms.TextInput(attrs={
            'placeholder': 'eg. my-username/my-project',
            'size': '80',
        })
    )
    description = forms.CharField(
        required=False,
        help_text=(
            "If you wish, say something about your team and "
            "goals for this contest."
        ),
        widget=forms.Textarea
    )
    users = forms.CharField(
        help_text="Enter a comma-separated list of the member usernames.",
        validators=[isCommaSeparatedUserList]
    )
    group_url = forms.CharField(
        label='Group URL',
        help_text=models.Entry._meta.get_field('group_url').help_text,
        widget=forms.TextInput(attrs={
            'size': '80',
        }),
        required=False,
    )

    def clean_description(self):
        """Strip HTML from the description."""
        return html2safehtml(self.cleaned_data['description'], safeTags)

    def clean_users(self):
        """Split users."""
        users = {u.strip() for u in self.cleaned_data['users'].split(',')}
        if self.current_user not in users:
            raise forms.ValidationError(
                "You cannot remove yourself from an entry. "
                "Other team members will be able to remove you."
            )
        return users

    def clean(self):
        """Validate fields that depend on each other.

        Here we just require open teams to provide a group URL.
        """
        data = super().clean()
        if data.get('is_open') and not data.get('group_url'):
            self.add_error('group_url', "Open teams must provide a Group URL.")

    class Meta:
        model = models.Entry
        fields = [
            'title',
            'github_repo',
            'description',
            'is_open',
            'group_url',
        ]


class AddEntryForm(BaseEntryForm):
    """Form for creating a new competition entry (game)."""
    name = forms.CharField(
        max_length=15,
        validators=[validators.validate_slug, isUnusedEntryName],
        required=True,
    )

    class Meta(BaseEntryForm.Meta):
        fields = BaseEntryForm.Meta.fields + [
            'name',
        ]


def entry_list(request, challenge_id):
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    entries = []
    finished = challenge.isCompFinished()
    all_done = challenge.isAllDone()

    may_rate = user_may_rate(challenge, request.user)
    # may rate at all
    may_rate = False
    if not all_done and not request.user.is_anonymous and challenge.isRatingOpen():
        username = request.user.username
        for e in models.Entry.objects.filter(challenge=challenge_id, users__username__exact=username):
            if e.has_final:
                may_rate = True
                break

    # random sorting per-user
    r = random.random()
    s = int(hashlib.md5(request.user.username.encode()).hexdigest()[:8], 16)
    random.seed(s)

    for entry in models.Entry.objects.filter(challenge=challenge_id):
        if all_done:
            files = []
            found_final = False
            for file in entry.file_set.filter(is_screenshot__exact=False):
                if file.is_final: found_final = True
                elif found_final: break
                files.append(file)
            if not found_final and finished:
                continue
        else:
            files = entry.file_set.filter(is_final__exact=True,
                is_screenshot__exact=False)
            if not files and finished:
                continue

        shots = entry.file_set.filter(is_screenshot__exact=True).order_by("-created")[:1]
        thumb = None
        if shots: thumb = shots[0]

        info = {
            'entry': entry,
            'name': entry.name,
            'game': entry.game,
            'title': entry.title,
            # 'description': description,
            'files': files,
            'sortname': random.random(),
            'may_rate': False,
            'thumb': thumb,
            'num_ratings': len(entry.rating_set.all()),
        }
        if may_rate and finished:
            info['has_rated'] = entry.has_rated(request.user)
        if may_rate and request.user not in entry.users.all():
            info['may_rate'] = True
        entries.append(info)

    # reset random generator
    random.seed(r)

    entries.sort(key=operator.itemgetter('sortname', 'num_ratings'))

    return render(request, 'challenge/entries.html', {
            'challenge': challenge,
            'entries': entries,
            'limited': finished,
            'finished': finished,
            'all_done': all_done,
            'user_may_rate': may_rate,
        }
    )


def user_may_rate(challenge, user):
    """Return True if the user may rate challenge entries at this time."""
    finished = challenge.isCompFinished()
    all_done = challenge.isAllDone()

    # may rate at all
    may_rate = False

    if not finished or all_done or not challenge.isRatingOpen():
        # Not in the rating period
        return False

    if user.is_anonymous:
        # Only logged-in users may rate
        return False

    # User may rate only iff they have final entries
    user_has_final = models.Entry.objects.filter(
        challenge__number=challenge.number,
        users__username__exact=user.username,
        has_final=True,
    ).count() > 0
    return user_has_final


def rating_dashboard(request, challenge_id):
    """A view of entries organised by which have been rated."""
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    if not user_may_rate(challenge, request.user):
        return HttpResponseForbidden()

    final_entries = models.Entry.objects.filter(
        challenge=challenge_id,
        has_final=True,
    ).annotate(
        author_count=md.Count('users', distinct=True),
        ratings_count=md.Count('rating'),
        ratings_nw=md.Count('rating', nonworking=True),
    ).select_related('user').prefetch_related(
        md.Prefetch(
            'entryaward_set',
            queryset=request.user.entryaward_set.all()
        )
    )
    user_ratings = models.Rating.objects.filter(
        user__username__exact=request.user.username,
        entry__challenge=challenge_id,
    )
    ratings_by_entry = {r.entry.pk: r for r in user_ratings}

    your_entries = set(models.Entry.objects.filter(
        challenge=challenge_id,
        users__username__exact=request.user.username,
    ).values_list('pk', flat=True))

    rated = []
    not_rated = []
    not_working = []
    yours = []
    for entry in final_entries:
        r = ratings_by_entry.get(entry.pk)
        if r:
            fun = r.fun
            prod = r.production
            inno = r.innovation
            nw = r.nonworking
            dq = r.disqualify
        else:
            fun = prod = inno = None
            dq = nw = False
        is_team = entry.author_count > 1
        info = {
            'name': entry.name,
            'game': entry.game,
            'title': entry.title,
            'owner': entry.title if is_team else entry.user.username,
            'is_team': is_team,
            'sortname': hash((request.user.username, entry.pk)),
            'fun': fun,
            'prod': prod,
            'inno': inno,
            'awards': entry.entryaward_set.filter(creator=request.user),
            'dq': dq,
            'nw_pct': (
                (entry.ratings_nw * 100.0 / entry.ratings_count)
                if entry.ratings_count != 0 else 0
            ),
        }
        if entry.pk in your_entries:
            yours.append(info)
        elif nw:
            not_working.append(info)
        elif r:
            rated.append(info)
        else:
            not_rated.append(info)

    for es in (rated, not_rated, yours):
        es.sort(key=lambda e: hash((request.user.username, e['name'])))

    return render(request, 'challenge/rating-dash.html', {
            'challenge': challenge,
            'rated': rated,
            'not_rated': not_rated,
            'not_working': not_working,
            'yours': yours,
        }
    )


@login_required
def entry_add(request, challenge_id):
    challenge = get_object_or_404(models.Challenge, pk=challenge_id)

    if not challenge.isRegoOpen():
        return HttpResponseRedirect(f"/{challenge_id}/")

    if challenge.isCompFinished():
        messages.error(request, 'Entry registration closed')
        return HttpResponseRedirect(f"/{challenge_id}/")

    if request.method == 'POST':
        f = AddEntryForm(request.POST)
        f.current_user = request.user.username

        if f.is_valid():
            entry = f.instance
            entry.challenge = challenge
            entry.user = request.user
            members = f.cleaned_data['users']

            entry.save()
            entry.users = models.User.objects.filter(username__in=members)

            short_description, truncated = summarise(entry.description)
            log_event(
                type='new-entry',
                challenge=entry.challenge.number,
                team=entry.title,
                members=list(members),
                name=entry.name,
                description=short_description,
                description_truncated=truncated,
            )

            messages.success(request, 'Entry created!')
            return HttpResponseRedirect(f"/e/{entry.name}/")
    else:
        f = AddEntryForm(initial={'users': request.user.username})

    return render(request, 'challenge/entry_add.html',
        {
            'challenge': challenge,
            'form': f,
            'is_member': True,
            'is_owner': True,
        }
    )


class RatingForm(forms.Form):
    fun = forms.IntegerField(widget=forms.Select( choices=models.RATING_CHOICES))
    innovation = forms.IntegerField(widget=forms.Select( choices=models.RATING_CHOICES))
    production = forms.IntegerField(widget=forms.Select( choices=models.RATING_CHOICES))
    nonworking = forms.TypedChoiceField(coerce=lambda x: x =='True',
        choices=((False, 'Playable'), (True, 'Failed to run/unplayable problems')),
        widget=forms.RadioSelect)
    #forms.BooleanField(required=False)
    disqualify = forms.BooleanField(required=False)
    comment = forms.CharField(widget=forms.Textarea, required=True)


def entry_display(request, entry_id):
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge
    user_list = entry.users.all()
    is_member = request.user in list(user_list)
    files = entry.file_set.filter(is_screenshot__exact=True).order_by("-created")[:1]
    thumb = None
    if files: thumb = files[0]

    # handle adding the ratings form and accepting ratings submissions
    f = None
    if entry.may_rate(request.user, challenge) and challenge.isRatingOpen():
        errors = {}

        # get existing scores
        rating = None
        for rating in entry.rating_set.filter(user__id__exact=request.user.id):
            break

        # fields for rating editing
        if request.method == 'POST':
            f = RatingForm(request.POST)
            if f.is_valid():
                if rating is not None:
                    # edit existing
                    rating.disqualify = f.cleaned_data['disqualify']
                    rating.nonworking = f.cleaned_data['nonworking']
                    rating.fun = f.cleaned_data['fun']
                    rating.innovation = f.cleaned_data['innovation']
                    rating.production = f.cleaned_data['production']
                    rating.comment = f.cleaned_data['comment']
                else:
                    # create new
                    rating = models.Rating(
                        entry=entry,
                        user=request.user,
                        disqualify=f.cleaned_data['disqualify'],
                        nonworking=f.cleaned_data['nonworking'],
                        fun=f.cleaned_data['fun'],
                        innovation=f.cleaned_data['innovation'],
                        production=f.cleaned_data['production'],
                        comment=f.cleaned_data['comment'],
                    )
                rating.save()
                messages.info(
                    request,
                    'Rating saved! &emsp; <a href="/{}/rating-dashboard">'
                    'Return to rating dashboard</a>'.format(
                        entry.challenge.number,
                    )
                )
                return HttpResponseRedirect(f"/e/{entry.name}/")
        elif rating is not None:
            data = dict(
                disqualify=rating.disqualify,
                nonworking=rating.nonworking,
                fun=rating.fun,
                innovation=rating.innovation,
                production=rating.production,
                comment=rating.comment
            )
            f = RatingForm(data)
        else:
            f = RatingForm()

    rating_results = False
    if challenge.isAllDone() and entry.has_final:
        # display ratings
        d = rating_results = entry.tally_ratings()
        d['dp'] = f"{int(d.get('disqualify', 0) * 100)}%"
        d['dnwp'] = f"{int(d.get('nonworking', 0) * 100)}%"

    join_requested = False

    if request.user.is_authenticated:
        if request.POST.get('action') == 'join':
            if not entry.is_open:
                messages.error(request,
                    "Sorry, {} is no longer accepting join requests.".format(
                        entry.title or entry.name
                    )
                )
            elif not entry.challenge.isRegoOpen():
                messages.error(request,
                    "You cannot join {} as the respective PyWeek challenge has ended.".format(
                        entry.title or entry.name
                    )
                )
            elif is_member:
                messages.error(
                    request,
                    "You are already a member of this team."
                )
            else:
                owner = entry.user
                addresses = [a.address for a in owner.emailaddress_set.all()]
                entry.join_requests.add(request.user)

                sending.send_template(
                    subject='Team membership request',
                    template_name='team-request',
                    recipients=addresses,
                    params={
                        'user': request.user,
                        'entry': entry,
                    },
                    reason='because you created an open team on pyweek.org.',
                )
                messages.success(request, "Request sent!")
                return HttpResponseRedirect(entry.get_absolute_url())

        join_requested = (
            entry.is_open and
            request.user in entry.join_requests.all()
        )

    return render(request, 'challenge/entry.html', {
            'challenge': challenge,
            'entry': entry,
            'files': entry.file_set.all(),
            'thumb': thumb,
            'diary_entries': entry.diary_entries(),
            'is_user': not request.user.is_anonymous,
            'is_member': is_member,
            'is_team': len(user_list) > 1,
            'is_owner': entry.user == request.user,
            'join_requested': join_requested,
            'form': f,
            'rating': rating_results,
            'awards': entry.entryaward_set.all(),
        }
    )


def entry_ratings(request, entry_id):
    entry = get_object_or_404(models.Entry, pk=entry_id)
    challenge = entry.challenge
    anon = request.user.is_anonymous
    super = not anon and request.user.is_superuser
    if not (challenge.isAllDone() or super):
        if not request.user.is_anonymous:
             messages.error(request, "You're not allowed to view ratings yet!")
        return HttpResponseRedirect(f'/e/{entry_id}/')
    user_list = entry.users.all()
    is_member = request.user in list(user_list)

    return render(request, 'challenge/entry_ratings.html', {
            'challenge': challenge,
            'entry': entry,
            'is_user': not request.user.is_anonymous,
            'is_member': is_member,
            'is_team': len(user_list) > 1,
            'is_owner': entry.user == request.user,
        }
    )


class EntryForm(BaseEntryForm):
    class Meta(BaseEntryForm.Meta):
        fields = BaseEntryForm.Meta.fields + [
            'game',
        ]


def entry_manage(request, entry_id):
    if request.user.is_anonymous:
        return HttpResponseRedirect('/login/')
    entry = get_object_or_404(models.Entry, pk=entry_id)

    user_list = entry.users.all()
    is_member = request.user in list(user_list)

    if not is_member:
        messages.error(request, "You're not allowed to manage this entry!")
        return HttpResponseRedirect(f'/e/{entry_id}/')

    if request.POST:
        f = EntryForm(request.POST, instance=entry)
        f.current_user = request.user.username

        if f.is_valid():
            entry = f.instance
            entry.save()

            team_members = f.cleaned_data['users']
            new_users = list(models.User.objects.filter(
                username__in=team_members,
            ))
            if len(new_users) != len(team_members):
                messages.error(request, 'Invalid team members list')
            else:
                entry.users = new_users
                messages.success(request, 'Changes saved!')
            return HttpResponseRedirect(f"/e/{entry_id}/")
    else:
        f = EntryForm(
            instance=entry,
            initial={
                'users': ', '.join(map(str, entry.users.all()))
            }
        )

    challenge = entry.challenge
    #form = forms.FormWrapper(f, new_data, errors)
    return render(request, 'challenge/entry_admin.html',
        {
            'challenge': challenge,
            'entry': entry,
            'form': f,
            'is_member': True,
            'is_owner': entry.user == request.user,
        }
    )


def entry_requests(request, entry_id):
    """Approve or reject join requests for a team."""
    back_to_entry = HttpResponseRedirect(f'/e/{entry_id}/')

    if request.user.is_anonymous:
        return back_to_entry

    entry = get_object_or_404(models.Entry, pk=entry_id)

    if not entry.is_open:
        messages.error(request, "This is not an open team.")
        return back_to_entry

    if entry.user != request.user:
        messages.error(
            request,
            "Only the team owner can accept membership requests."
        )
        return back_to_entry

    if request.method == 'POST':
        data = request.POST
        added = set()
        rejected = set()
        for u in list(entry.join_requests.all()):
            action = request.POST.get('user:' + u.username)
            if action == 'approve':
                # TODO: send e-mail
                entry.users.add(u)
                entry.join_requests.remove(u)
                added.add(u)
            elif action == 'reject':
                # TODO: send e-mail
                entry.join_requests.remove(u)
                rejected.add(u)

        team_name = entry.title or entry.name

        if added:
            addresses = [
                a.address for a in
                EmailAddress.objects.filter(user__in=added)
            ]
            sending.send_template(
                subject=f'{team_name} team membership accepted',
                template_name='team-request-accepted',
                recipients=addresses,
                params={
                    'entry': entry,
                },
                reason='because you requested to join this team.',
            )

        if added or rejected:
            msgs = []
            if added:
                msgs.append(f'added {len(added)} new team members')
            if rejected:
                msgs.append(
                    f'rejected {len(rejected)} membership requests'
                )
            messages.success(request, ' and '.join(msgs).capitalize())
            return back_to_entry
        else:
            messages.error(request, 'No changes made.')


    return render(
        request,
        'challenge/entry_requests.html',
        {
            'entry': entry,
            'requesters': entry.join_requests.all()
        }
    )
