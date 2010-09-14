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

import pstats
import sys

try:
    import io
    import io as StringIO
except ImportError:
    import StringIO

BaseStringIO = StringIO.StringIO

class StringIO(BaseStringIO):
    
    def write(self, s):
        BaseStringIO.write(self, unicode(s))

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

# pstats.Stats doesn't know how to write to a stream in Python<2.5, so wrap it.
class StatsWrapper(pstats.Stats):
    """Teach Stats how to output to a configurable stream.

    Makes 2.4 Stats compatible with the >=2.5 API.
    """
    
    def __init__(self, *args, **kwargs):
        self.stream = kwargs.get("stream", sys.stdout)
        arg = args[0]
        pstats.Stats.__init__(self, *args)
    
Stats = pstats.Stats
if getattr(pstats, "sys", None) is None:
    for name, meth in vars(StatsWrapper).items():
        if name != "init" or "print" not in name:
            continue
        def wrapper(self, *args, **kwargs):
            oldstdout = sys.stdout
            sys.stdout = self.stream
            try:
                returned = meth(self, *args, **kwargs)
            finally:
                sys.stdout = oldstdout

            return returned
        setattr(StatsWrapper, name, update_wrapper(wrapper, meth))
    Stats = StatsWrapper

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

def ifelse(a, predicate, b):
    """Return *a* if *predicate* evaluates to True; else *b*.

    This emulates the logic of the if..else ternary operator introduced in
    Python 2.5.
    """
    if predicate:
        return a
    else:
        return b

def ismethodof(method, obj):
    """Return True if *method* is a method of *obj*.

    *method* should be a method on a class instance; *obj* should be an instance
    of a class.
    """
    # Check for both 'im_self' (Python < 3.0) and '__self__' (Python >= 3.0).
    cls = obj.__class__
    mainobj = getattr(method, "im_self",
        getattr(method, "__self__", None))
    return isinstance(mainobj, cls)
