import json

from django.conf import settings
from django.db import models
from django.contrib.contenttypes.fields import (
    GenericForeignKey, GenericRelation
)
from django.contrib.contenttypes.models import ContentType


class Event(models.Model):
    """An event in the activity stream."""
    date = models.DateTimeField(auto_now_add=True)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        on_delete=models.SET_NULL,
    )
    type = models.CharField(max_length=16)
    data = models.TextField()

    target_content_type = models.ForeignKey(
        ContentType,
        null=True,
        on_delete=models.SET_NULL,
    )
    target_id = models.PositiveIntegerField(null=True)
    target = GenericForeignKey(
        'target_content_type', 'target_id',
    )

    _params = None

    @property
    def params(self):
        if self._params is None:
            self._params = json.loads(self.data)
        return self._params

    class Meta:
        ordering = ['-date']

    @property
    def template_name(self):
        return f'activity/{self.type}.html'


def log_event(type, user=None, target=None, **kwargs):
    """Log an event in the activity feed.

    :param str type: The type of event. Corresponds to the template used.
    :param User user: The user who performed the event, or None if the event
                      was not performed by a user.
    :param models.Model target: An optional model that the event relates to.
    :param kwargs: Arbitrary JSON-serialisable properties that will be
                   available in the template for the event.

    """
    if len(type) > 16:
        raise ValueError("type must be less than 16 characters")
    ev = Event(
        type=type,
        user=user,
        target=target,
        data=json.dumps(kwargs),
    )
    ev.save()


def EventRelation():
    """A reverse relation for the event."""
    return GenericRelation(
        Event,
        content_type_field='target_content_type',
        object_id_field='target_id',
    )

