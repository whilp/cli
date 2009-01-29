"""cli.util - miscellaneous helpers

Copyright (c) 2008-2009 Will Maier <will@m.aier.us>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
from UserDict import UserDict

Nothing = object()

class AttributeDict(UserDict, object):
    """A dict that maps its keys to attributes."""

    def __getattribute__(self, attr):
        """Fetch an attribute.

        If the instance has the requested attribute, return it. If
        not, look for the attribute in the .data dict. If the
        requested attribute can't be found in either location, raise
        AttributeError.
        """
        try:
            value = super(AttributeDict, self).__getattribute__(attr)
        except AttributeError:
            data = super(AttributeDict, self).__getattribute__("data")
            value = data.get(attr, Nothing)
            if value is Nothing:
                raise

        return value

def plural(number):
    """Return 's' if number is != 1."""
    return number != 1 and 's' or ''

def Boolean(thing):
    """Decide if 'thing' is True or False.

    If thing is a string, convert it to lower case and, if it starts
    with 'y' or 't' (as in 'yes' or 'true'), return True. If it
    starts with some other character, return False. Otherwise,
    return True if 'thing' is True (in the Pythonic sense).
    """
    if callable(getattr(thing, 'lower', None)):
        thing = thing.lower()
        if thing[0] in 'yt':
            return True
        else:
            return False
    elif thing:
        return True
    else:
        return False
