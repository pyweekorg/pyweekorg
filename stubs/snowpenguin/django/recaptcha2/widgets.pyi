from django.forms.widgets import Input, Widget
from typing import Any, Optional

class ReCaptchaWidget(Widget):
    container_id: Any
    explicit: Any
    theme: Any
    type: Any
    size: Any
    tabindex: Any
    callback: Any
    expired_callback: Any
    attrs: Any

    def __init__(
        self,
        explicit: bool = ...,
        container_id: Optional[str] = ...,
        theme: Optional[str] = ...,
        type: Optional[str] = ...,
        size: Optional[str] = ...,
        tabindex: Optional[str] = ...,
        callback: Optional[str] = ...,
        expired_callback: Optional[str] = ...,
        public_key: Optional[str] = ...,
        attrs: dict[str, Any] = ...,
        *args,
        **kwargs
    ) -> None: ...

    def render(self, name, value, attrs: Any | None = ..., *args, **kwargs): ...

    def value_from_datadict(self, data, files, name): ...


class ReCaptchaHiddenInput(Input):
    input_type: str
    def render(self, name, value, attrs: Any | None = ..., renderer: Any | None = ...): ...
    def value_from_datadict(self, data, files, name): ...
