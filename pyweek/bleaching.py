"""HTML sanitisation functions.

Historically we used a package called stripogram
(https://pypi.org/project/stripogram/), which has long since become
unmaintained, and only works on Python 2.

Here we provide a similar interface, implemented using bleach.
"""
import bleach


SAFE_TAGS = '''strong em blockquote pre b a i br img table tr th td pre p dl dd dt ul ol li span div'''.split()

SAFE_ATTRIBUTES = {
    'a': ['href', 'title'],
    'img': ['src', 'alt'],
}


def html2safehtml(text: str, tags: list[str] = SAFE_TAGS) -> str:
    """Return a cleaned version of the given text.

    This is a wrapper around bleach to centralise the options we pass to it.
    """
    return bleach.clean(
        text,
        tags=tags,
        attributes=SAFE_ATTRIBUTES,
        strip=True
    )


def html2text(text: str) -> str:
    """Remove all tags from the given HTML string."""
    return bleach.clean(text, tags=(), strip=True)
