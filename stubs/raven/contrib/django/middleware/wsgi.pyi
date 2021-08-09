from typing import Any, Iterable, Callable

StartResponse = Callable[[str, list[tuple[str, str]]], None]
Environ = dict[str, Any]
WSGI = Callable[[Environ, StartResponse], Iterable[bytes]]

class Sentry:
    def __init__(self, application: WSGI) -> None: ...

    def __call__(
        self,
        environ: Environ,
        start_response: StartResponse
    ) -> Iterable[bytes]: ...
