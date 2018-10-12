from django.conf.urls import url, include
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import django.views.static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

import pyweek.mail.urls
import pyweek.activity.urls


admin.autodiscover()

urlpatterns = [
    url(r'^admin/', include(admin.site.urls)),
    url(r'^emails/', include(pyweek.mail.urls)),
    url(r'^latest/', include(pyweek.activity.urls)),
    url(r'', include('pyweek.challenge.urls')),
]

# These rules automatically only apply when DEBUG is True
urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
