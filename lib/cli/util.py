"""cli.util - miscellaneous helpers

Copyright (c) 2008-2010 Will Maier <will@m.aier.us>

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

import sys

try:
    import cStringIO as StringIO
except ImportError:
    try:
        import StringIO
    except ImportError:
        import io as StringIO

StringIO = StringIO.StringIO

class update_wrapper(object):
    assignments = ('__module__', '__name__', '__doc__')
    updates = ('__dict__',)

    def __call__(self, wrapper, wrapped):
        """Update callable wrapper so it looks like callable wrapped.
    
        Based on functools.update_wrapper (used only for compatibility on
        Python <= 2.5).
        """
        for attr in self.assignments:
            setattr(wrapper, attr, getattr(wrapped, attr))
        for attr in self.updates:
            getattr(wrapper, attr).update(getattr(wrapper, attr, {}))
    
        return wrapper

update_wrapper = update_wrapper()

def fmtsec(seconds):
    if seconds < 0:
        return '-' + fmtsec(-seconds)
    elif seconds == 0:
        return '0 s'

    prefixes = " munp"
    powers = range(0, 3 * len(prefixes) + 1, 3)

    prefix = ''
    for power, prefix in zip(powers, prefixes):
        if seconds >= pow(10.0, -power):
            seconds *= pow(10.0, power)
            break

    formats = [
        (1e9, "%.4g"),
        (1e6, "%.0f"),
        (1e5, "%.1f"),
        (1e4, "%.2f"),
        (1e3, "%.3f"),
        (1e2, "%.4f"),
        (1e1, "%.5f"),
        (1e0, "%.6f"),
    ]

    for threshold, format in formats:
        if seconds >= threshold:
            break

    format += " %ss"
    return format % (seconds, prefix)

def trim(string):
    """Trim whitespace from strings.

    This implementation is a (nearly) verbatim copy of that proposed in PEP-257:

        http://www.python.org/dev/peps/pep-0257/
    """
    if not string:
        return ''
    # Convert tabs to spaces (following the normal Python rules)
    # and split into a list of lines:
    lines = string.expandtabs().splitlines()
    # Determine minimum indentation (first line doesn't count):
    indent = sys.maxint
    for line in lines[1:]:
        stripped = line.lstrip()
        if stripped:
            indent = min(indent, len(line) - len(stripped))
    # Remove indentation (first line is special):
    trimmed = [lines[0].strip()]
    if indent < sys.maxint:
        for line in lines[1:]:
            trimmed.append(line[indent:].rstrip())
    # Strip off trailing and leading blank lines:
    while trimmed and not trimmed[-1]:
        trimmed.pop()
    while trimmed and not trimmed[0]:
        trimmed.pop(0)
    # Return a single string:
    return '\n'.join(trimmed) + "\n"
