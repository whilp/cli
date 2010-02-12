"""cli.profiler - CLI profiler

Copyright (c) 2009-2010 Will Maier <will@m.aier.us>

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

try:
    from functools import update_wrapper
except ImportError:	# pragma: no cover
    from .util import update_wrapper

from .util import fmtsec

class Profiler(object):

    def __init__(self, stdout=None, anonymous=False, count=1000, repeat=3):
        self.stdout = stdout is None and sys.stdout or stdout
        self.anonymous = anonymous
        self.count = count
        self.repeat = repeat

    def wrap(self, wrapper, wrapped):
        update_wrapper(wrapper, wrapped)

        if self.anonymous or self.isanon(wrapped.__name__):
            return wrapper()
        else:
            return wrapper

    def isanon(self, name):
        return name.startswith("__profiler_") or \
            name == "anonymous"

    def deterministic(self, func):
        from pstats import Stats

        try:
            from cProfile import Profile
        except ImportError:	# pragma: no cover
            from profile import Profile
        profiler = Profile()

        def wrapper(*args, **kwargs):
            self.stdout.write("===> Profiling %s:\n" % func.__name__)
            profiler.runcall(func, *args, **kwargs)
            stats = Stats(profiler, stream=self.stdout)
            stats.strip_dirs().sort_stats(-1).print_stats()

        return self.wrap(wrapper, func)

    def statistical(self, func):
        try:
            from timeit import default_timer as timer
        except ImportError:	# pragma: no cover
            from time import time as timer

        def timeit(func, *args, **kwargs):
            cumulative = 0
            for i in range(self.count):
                start = timer()
                func(*args, **kwargs)
                stop = timer()
                cumulative += stop - start

            return cumulative

        def repeat(func, *args, **kwargs):
            return [timeit(func, *args, **kwargs) for i in range(self.repeat)]

        def wrapper(*args, **kwargs):
            self.stdout.write("===> Profiling %s: " % func.__name__)
            result = min(repeat(func, *args, **kwargs))
            self.stdout.write("%d loops, best of %d: %s per loop\n" % (
                self.count, self.repeat, fmtsec(result/self.count)))

        return self.wrap(wrapper, func)

    __call__ = deterministic
