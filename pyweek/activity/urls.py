from django.conf.urls import url

from .views import timeline


urlpatterns = [
    url('^$', timeline, name='timeline'),
]
