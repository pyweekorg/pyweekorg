from typing import Any, Union

Priority = Union[None, int, str]

def get_priority(priority: Priority) -> int: ...
def send_mail(
    subject: str,
    message: str,
    from_email: str,
    recipient_list: list[str],
    priority: Priority = ...,
    fail_silently: bool = ...,
    auth_user: Any = ...,
    auth_password: Any = ...
): ...
def send_html_mail(
    subject: str,
    message: str,
    message_html: str,
    from_email: str,
    recipient_list: list[str],
    priority: Priority = ...,
    fail_silently: bool = ...,
    auth_user: Any = ...,
    auth_password: Any = ...,
    headers=...
): ...
def send_mass_mail(
    datatuple: list[tuple[str, str, str, str]],
    fail_silently: bool = ...,
    auth_user: Any | None = ...,
    auth_password: Any = ...,
    connection: Any | None = ...
): ...
def mail_admins(
    subject,
    message,
    fail_silently: bool = ...,
    connection: Any | None = ...,
    priority: Priority = ...
): ...
def mail_managers(
    subject: str,
    message: str,
    fail_silently: bool = ...,
    connection: Any = ...,
    priority: Priority = ...
): ...
