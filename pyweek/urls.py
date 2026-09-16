from django.urls import URLPattern, URLResolver, include, path, re_path
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
import django.views.static
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.base import RedirectView

admin.autodiscover()

urlpatterns: list[URLPattern | URLResolver] = [
    path("admin/", admin.site.urls),
    path("emails/", include("pyweek.mail.urls")),
    path("latest/", include("pyweek.activity.urls")),
    re_path(
        r"^media/dl/(?P<path>.*)",
        RedirectView.as_view(url=settings.MEDIA_URL + "%(path)s"),
    ),
    path("", include("pyweek.challenge.urls")),
]
