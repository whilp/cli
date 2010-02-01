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

import logging
import os
import sys

from logging import Formatter, StreamHandler

from cli.ext import argparse
from cli.profiler import Profiler

__all__ = ["Application", "App", "CommandLineLogger", "CommandLineApp", "LoggingApp"]


class FileHandler(logging.FileHandler):

    def close(self):
        """Override close().
        
        We leave the file open because the application may have
        multiple threads that still need to write to it. Python
        should GC the fd when it goes out of scope, anyway.
        """
        pass

class NullHandler(logging.Handler):
    """A blackhole handler.

    NullHandler simply ignores all messages it receives.
    """

    def emit(self, record):
        """Ignore the record."""
        pass

class CommandLineLogger(logging.Logger):
    """Provide extra configuration smarts for loggers.

    In addition to the powers of a regular logger, a CommandLineLogger can
    set its verbosity levels based on a populated argparse.Namespace.
    """
    default_level = logging.WARN
    silent_level = logging.CRITICAL

    def setLevel(self, ns=None):
        """Set the logging level of this handler.

        ns is an object (like an argparse.Namespace) with the following
        attributes:
            
            verbose     integer
            quiet       integer
            silent      True/False
        """
        level = 10 * (ns.quiet - ns.verbose)

        if ns.silent:
            level = self.silent_level
        elif level <= logging.NOTSET:
            level = logging.DEBUG

        self.level = level

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

        returned = self.main(self, *self.args)

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

class LoggingApp(CommandLineApp):
    """A command-line application that knows how to log.

    A LoggingApp provides a 'log' attribute, which is a logger (from
    the logging module). The logger's verbosity is controlled via
    handy options ('verbose', 'quiet', 'silent') and sends its
    output to stderr by default (though it will log to a file if the
    'logfile' attribute is not None). Non-stderr streams can be
    requested by setting the 'stream' attribute to something besides
    None.
    """

    def __init__(self, main, stream=sys.stdout, logfile=None,
            message_format="%(message)s", 
            date_format="%(asctime)s %(message)s", **kwargs):
        self.logfile = logfile
        self.stream = stream
        self.message_format = message_format
        self.date_format = date_format
        super(LoggingApp, self).__init__(main, **kwargs)

    def setup(self):
        super(LoggingApp, self).setup()

        # Add logging-related options.
        self.add_param("-l", "--logfile", default=self.logfile, 
                help="log to file (default: log to stdout)", action="count")
        self.add_param("-q", "--quiet", default=0, help="decrease the verbosity",
                action="count")
        self.add_param("-s", "--silent", default=False, help="only log warnings",
                action="store_true")
        self.add_param("-v", "--verbose", default=0, help="raise the verbosity",
                action="count")

        # Create logger.
        logging.setLoggerClass(CommandLineLogger)
        self.log = logging.getLogger(self.name)

        # Create formatters.
        message_formatter = Formatter(self.message_format)
        date_formatter = Formatter(self.date_format)
        verbose_formatter = Formatter()
        self.formatter = message_formatter

        self.log.level = self.log.default_level

    def pre_run(self):
        """Configure logging before running the app."""
        super(LoggingApp, self).pre_run()
        self.log.setLevel(self.args)

        if self.logfile is not None:
            file_handler = FileHandler(self.logfile)
            file_handler.setFormatter(self.formatter)
            self.log.addHandler(file_handler)
        elif self.stream is not None:
            stream_handler = StreamHandler(self.stream)
            stream_handler.setFormatter(self.formatter)
            self.log.addHandler(stream_handler)

        # The null handler simply drops all messages.
        if not self.log.handlers:
            self.log.addHandler(NullHandler())

class DaemonizingApp(LoggingApp):
    """A command-line application that knows how to daemonize.
    """

    def __init__(self, main, pidfile=None,
            chdir='/', null="/dev/null", **kwargs):
        self.pidfile = pidfile
        self.chdir = chdir
        self.null = null
        super(DaemonizingApp, self).__init__(main, **kwargs)

    def setup(self):
        super(DaemonizingApp, self).setup()

        # Add daemonizing options.
        self.add_param("-d", "--daemonize", default=False, action="store_true",
                help="run the application in the background")
        self.add_param("-u", "--user", default=None, 
                help="change to USER[:GROUP] after daemonizing")
        self.add_param("-p", "--pidfile", default=None, 
                help="write PID to PIDFILE after daemonizing")

    def daemonize(self):
        """Daemonize the application.
        
        Send the application to the background, redirecting
        stdin/stdout and changing its UID if requested.
        """
        if os.fork(): sys.exit(0)
        os.umask(0) 
        os.setsid() 
        if os.fork(): sys.exit(0)

        self.stdout.flush()
        self.stderr.flush()
        si = open(self.null, 'r')
        so = open(self.null, 'a+')
        se = open(self.null, 'a+', 0)
        os.dup2(si.fileno(), self.stdin.fileno())
        os.dup2(so.fileno(), self.stdout.fileno())
        os.dup2(se.fileno(), self.stderr.fileno())

        if self.args.pidfile:
            self.log.debug("Writing pidfile %s", self.args.pidfile)
            pidfile = open(self.args.pidfile, 'w')
            pidfile.write('%i\n' % os.getpid())
            pidfile.close()

        if self.args.user:
            import grp
            import pwd
            delim = ':'
            user, sep, group = self.args.user.partition(delim)

            # If group isn't specified, try to use the username as
            # the group.
            if delim != sep:
                group = user
            self.log.debug("Changing to %s:%s", user, group)
            os.setgid(grp.getgrnam(group).gr_gid)
            os.setuid(pwd.getpwnam(user).pw_uid)

        self.log.debug("Changing directory to %s", self.chdir)
        os.chdir(self.chdir)

        return True

def test(app, *args):
    pass

App = LoggingApp
