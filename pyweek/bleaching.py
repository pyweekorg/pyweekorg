"""HTML sanitisation functions.

Historically we used a package called stripogram
(https://pypi.org/project/stripogram/), which has long since become
unmaintained, and only works on Python 2.

Here we provide a similar interface, implemented using bleach.
"""
import bleach


def html2safehtml(text: str):
    """Return a cleaned version of the given text.

    This is a wrapper around bleach to centralise the options we pass to it.
    """
    return bleach.clean(text, strip=True)


def html2text(text: str):
    """Remove all tags from the given HTML string."""
    return bleach.clean(text, tags=(), strip=True)
