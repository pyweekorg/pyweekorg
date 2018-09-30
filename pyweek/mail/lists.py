"""Configuration for mailing lists - sets of users to e-mail.

All list providers should return an iterable of users.

"""


LISTS = {}

def register(name):
    """Decorator to register the list provider."""
    def dec(f):
        return f
    return dec


def all_users():
    """A list of all users."""
