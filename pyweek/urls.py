from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import django.views.static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import RedirectView

import pyweek.mail.urls
import pyweek.activity.urls


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^emails/', include(pyweek.mail.urls)),
    url(r'^latest/', include(pyweek.activity.urls)),
    url(r'^media/dl/(?P<path>.*)',
        RedirectView.as_view(url=settings.MEDIA_URL + '%(path)s')),
    url(r'', include('pyweek.challenge.urls')),
]
