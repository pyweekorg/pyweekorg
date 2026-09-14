from django.urls import re_path

from .views import timeline


urlpatterns = [
    re_path(r"^$", timeline, name="timeline"),
]
