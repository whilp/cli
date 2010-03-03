"""\
:mod:`cli.test` -- functional and unit test support
---------------------------------------------------

This module provides support for easily writing both functional and
unit tests for your scripts.
"""

__license__ = """Copyright (c) 2008-2010 Will Maier <will@m.aier.us>

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
    import unittest2 as unittest
except ImportError:
    import unittest

__all__ = ["AppTest"]

class AppTest(unittest.TestCase):
    """An application test, based on :class:`unittest.TestCase`.

    :class:`AppTest` provides a simple :meth:`setUp` method to
    instantiate :attr:`app_cls`, your application. :attr:`default_kwargs`
    will be passed to the new application then.
    """
    app_cls = None
    """An application, usually descended from :class:`cli.Application`."""

    default_kwargs = {
        "argv": [],
        "exit_after_main": False
    }
    """Default keyword arguments that will be passed to the new App instance.

    By default, the application won't see any command line arguments and
    will not raise SystemExit when the :func:`main` function returns.
    """

    def setUp(self):
        """Set up the application.

        :meth:`setUp` instantiates :attr:`app_cls` and stores it
        :at attr:`app`. Test methods should call the application's
        ::meth:`setup`, :meth:`pre_run` and :meth:`run` methods as
        necessary.
        """
        kwargs = self.default_kwargs.copy()
        kwargs.update(getattr(self, "kwargs", {}))
        @self.app_cls(**kwargs)
        def app(app):
            pass
        self.app = app
