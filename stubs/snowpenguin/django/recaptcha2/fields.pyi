from django import forms
from snowpenguin.django.recaptcha2.widgets import ReCaptchaWidget as ReCaptchaWidget
from typing import Any, Optional


class ReCaptchaField(forms.CharField):
    def __init__(
        self,
        attrs: dict[str, Any] = ...,
        *args,
        private_key: Optional[str] = None,
        public_key: Optional[str] = None,
        widget: Optional[forms.Widget] = None,
        **kwargs
    ) -> None: ...

    def clean(self, values: list[str]) -> str: ...
