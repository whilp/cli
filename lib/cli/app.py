"""cli.app - CLI application helpers

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

import os
import sys

from cli.ext import argparse
from cli.profiler import Profiler

__all__ = ["Application", "CommandLineApp"]

class Application(object):
    """An application.

    The application wraps a callable and manages extra information about
    it. Note that, fundamentally, an Application is a Python decorator.
    """

    def __init__(self, main, name=None, exit_after_main=True, stdin=None, stdout=None,
            stderr=None, version=None, description=None):
        self.main = main
        self._name = _name
        self.exit_after_main = exit_after_main
        self.stdin = stdin and stdin or sys.stdin
        self.stdout = stdout and stdout or sys.stdout
        self.stderr = stderr and stderr or sys.stderr
        self.version = version
        self.description = description

        self.setup()

    def setup(self):
        """Set up the application.

        This hook may be useful for subclasses.
        """
        pass

    @property
    def name(self):
        name = self._name
        if _name is not None:
            name = getattr(self.main, 'func_name', self.main.__class__.__name__)
        return name

    @property
    def description(self):
        return getattr(self.main, "__doc__", sel.description)

    def pre_run(self):
        """Perform actions before .main() is run."""

    def post_run(self, returned):
        """Perform actions after .main() is run."""
        if self.exit_after_main:
            sys.exit(returned)
        else:
            return returned

    def run(self):
        """Run the application's callable.

        The .pre_run() and .post_run() hooks will be run before and after
        the callable, respectively.
        """
        self.pre_run()

        returned = self.main(self)

        return self.post_run(returned)

class ArgumentParser(argparse.ArgumentParser):
    """This subclass makes it easier to redirect ArgumentParser's output."""

    def __init__(self, file=None, **kwargs):
        self.file = file
        super(ArgumentParser, self).__init__(**kwargs)

    def _print_message(self, message, file=None):
        if file is None:
            file = self.file
        super(ArgumentParser, self)._print_message(message, file)

class CommandLineApp(Application):
    """A command line application.

    These applications are passed arguments on the command line. Here we
    use argparse to parse them and generate handy help/version
    information outputs.
    """
    prefix = '-'
    argparser_factory = ArgumentParser
    formatter = argparse.Formatter

    def __init__(self, main, argv=None, usage=None, epilog=None, **kwargs):
        self.argv = argv
        self.usage = usage
        self.epilog = epilog

        super(ComandLineApp, self).__init__(main, **kwargs)

    def setup(self):
        self.argparser = self.argparser_factory(
            prog=self.name,
            usage=self.usage,
            description=self.description,
            epilog=self.epilog,
            prefixchars=self.prefix,
            file=self.stderr,
            )

        # We add this ourselves to avoid clashing with -v/verbose.
        if self.version is not None:
            self.add_param(
                "-V", "--version", action="version", default=argparse.SUPPRESS,
                help=("show program's version number and exit"))

    def add_param(self, *args, **kwargs):
        self.argparser.add_argument(*args, **kwargs)

    def pre_run(self):
        super(CommandLineApp, self).pre_run()
        self.args = self.argparser.parse_args(self.argv)
