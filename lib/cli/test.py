"""\
:mod:`cli.test` -- functional and unit test support
---------------------------------------------------

.. versionadded:: 1.0.2

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

import os

from shutil import rmtree
from tempfile import mkdtemp

try:
    import unittest2 as unittest
except ImportError:
    import unittest

from cli.ext import scripttest
from cli.util import trim

__all__ = ["AppTest", "FunctionalTest"]

class AppTest(unittest.TestCase):
    """An application test, based on :class:`unittest.TestCase`.

    :class:`AppTest` provides a simple :meth:`setUp` method
    to instantiate :attr:`app_cls`, your application's class.
    :attr:`default_kwargs` will be passed to the new application then.
    """
    app_cls = None
    """An application, usually descended from :class:`cli.app.Application`."""

    default_kwargs = {
        "argv": [],
        "exit_after_main": False
    }
    """Default keyword arguments that will be passed to the new :class:`cli.app.Application` instance.

    By default, the application won't see any command line arguments and
    will not raise SystemExit when the :func:`main` function returns.
    """

    def setUp(self):
        """Set up the application.

        :meth:`setUp` instantiates :attr:`app_cls` and
        stores it at :attr:`app`. Test methods should call
        the application's :meth:`cli.app.Application.setup`,
        :meth:`cli.app.Application.pre_run` and
        :meth:`cli.app.Application.run` methods as necessary.
        """
        kwargs = self.default_kwargs.copy()
        kwargs.update(getattr(self, "kwargs", {}))
        @self.app_cls(**kwargs)
        def app(app):
            pass
        self.app = app

class FunctionalTest(unittest.TestCase):
    """A functional test, also based on :class:`unittest.TestCase`.

    Functional tests monitor an application's 'macro' behavior, making
    it easy to spot regressions. They can also be simpler to write and
    maintain as they don't rely on any application internals.

    The :class:`FunctionalTest` will look for scripts to run under
    :attr:`scriptdir`. It uses :class:`scripttest.TestFileEnvironment`
    to provide temporary working areas for the scripts; these scratch
    areas will be created under :attr:`testdir` (and are created and
    removed before and after each test is run).
    """
    testdir = None
    scriptdir = None

    def setUp(self):
        """Prepare for the functional test.

        :meth:`setUp` creates the test's working directory. If
        the :mod:`unittest2` package is present, it also makes sure that
        differences in the test's standard err and output are presented
        using :class:`unittest2.TestCase.assertMultiLineEqual`. Finally,
        :meth:`setUp` instantiates the
        :class:`scripttest.TestFileEnvironment` and stores it at
        :attr:`env`.
        """
        self._testdir = self.testdir
        if self._testdir is None:
            self._testdir = mkdtemp(prefix="functests-")
        if not os.path.isdir(self._testdir):
            os.mkdir(self._testdir)
        self.env = scripttest.TestFileEnvironment(os.path.join(self._testdir, "scripttest"))

        addTypeEqualityFunc = getattr(self, "addTypeEqualityFunc", None)
        if callable(addTypeEqualityFunc):
            addTypeEqualityFunc(str, "assertMultiLineEqual")

    def tearDown(self):
        """Clean up after the test.

        :meth:`tearDown` removes the temporary working directory created
        during :meth:`setUp`.
        """
        rmtree(self._testdir)

    def run_script(self, script, *args, **kwargs):
        """Run a test script.

        *script* is prepended with the path to :attr:`scriptdir` before
        it, *args* and *kwargs* are passed to :attr:`env`.
        """
        script = os.path.join(self.scriptdir, script)
        return self.env.run(script, *args, **kwargs)

    def assertScriptDoes(self, result, stdout='', stderr='', returncode=0, trim_output=True):
        """Fail if the result object's stdout, stderr and returncode are unexpected.

        *result* is usually a :class:`scripttest.ProcResult` with
        stdout, stderr and returncode attributes.
        """
        if trim_output:
            stdout, stderr = trim(stdout), trim(stderr)
        self.assertEqual(result.returncode, returncode,
            "expected returncode %d, got %d" % (result.returncode, returncode))
        self.assertEqual(result.stdout, stdout,
            "unexpected output on stdout")
        self.assertEqual(result.stderr, stderr,
            "unexpected output on stderr")
