"""cli.app - CLI application helpers

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

import datetime
import logging
import optparse
import os
import sys
import types
import unittest

from ConfigParser import ConfigParser
from UserDict import UserDict
from UserList import UserList
from inspect import getargs, isclass, isfunction, ismethod
from logging import Formatter, StreamHandler
from operator import itemgetter, attrgetter
from string import letters

from ext import argparse
from util import AttributeDict, Boolean, Nothing, plural

try:
    from functools import update_wrapper
except ImportError:
    from util import update_wrapper

__all__ = ["App", "EnvironParameterHandler", "CLIParameterHandler",
        "CommandLineApp", "LoggingApp"]

Nothing = object()

class DefaultSentinel(int, object):
    """A default sentinel.

    DefaultSentinels are used to differentiate between actual
    defaults and optparse defaults. Since optparse wants to call
    default.__add__() when the action is 'count', DefaultSentinel
    needs to inherit from int, too.
    """

Default = DefaultSentinel()

class Error(Exception):
    pass

class MainError(Error):
    pass

class ParameterError(Error):
    pass

def fmtsec(seconds):
    if seconds < 0:
        return '-' + self.seconds(-seconds)

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


class Profiler(object):

    def __init__(self, stdout=None, anonymous=False, count=1000, repeat=3):
        self.stdout = stdout is None and sys.stdout or stdout
        self.anonymous = anonymous
        self.count = count
        self.repeat = repeat

    def wrap(self, wrapper, wrapped):
        update_wrapper(wrapper, wrapped)

        if self.anonymous or self.isanon(wrapped.func_name):
            return wrapper()
        else:
            return wrapper

    def isanon(self, func_name):
        return func_name.startswith("__profiler_") or \
            func_name == "anonymous"

    def deterministic(self, func):
        from pstats import Stats

        try:
            from cProfile import Profile
        except ImportError:
            from profile import Profile
        profiler = Profile()

        def wrapper(*args, **kwargs):
            self.stdout.write("===> Profiling %s:\n" % func.func_name)
            profiler.runcall(func, *args, **kwargs)
            stats = Stats(profiler, stream=self.stdout)
            stats.strip_dirs().sort_stats(-1).print_stats()

        return self.wrap(wrapper, func)

    def statistical(self, func):
        try:
            from timeit import default_timer as timer
        except ImportError:
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
            self.stdout.write("===> Profiling %s: " % func.func_name)
            result = min(repeat(func, *args, **kwargs))
            self.stdout.write("%d loops, best of %d: %s per loop\n" % (
                self.count, self.repeat, fmtsec(result/self.count)))

        return self.wrap(wrapper, func)

    __call__ = deterministic

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

class CLILogger(logging.Logger):
    """Provide extra configuration smarts for loggers.

    In addition to the powers of a regular logger, a CLILogger can
    interpret optparseOptionGroups, using the 'verbose', 'quiet' and
    'silent' options to set the logger's verbosity.
    """
    default_level = logging.WARN
    silent_level = logging.CRITICAL

    def setLevel(self, level=0, opts=None):
        """Set the logging level of this handler.

        If 'level' is an optparse.OptionGroup, choose the level
        based on the 'verbose', 'silent' and 'quiet' attributes.
        """
        if opts is None:
            return logging.Logger.setLevel(self, level)

        level = self.default_level + (10 * (int(opts.quiet) - int(opts.verbose)))

        if opts.silent:
            level = self.silent_level
        elif level <= logging.NOTSET:
            level = logging.DEBUG

        self.level = level

class ParameterPath(UserList):

    def __str__(self):
        delim = Parameter.delim
        path = [x.name for x in self.data]
        return delim.join(path).lstrip(delim)

class Parameter(AttributeDict):
    """An application run-time parameter.

    Parameters influence the way an application runs and allow users
    to adjust general behavior. The Parameter abstraction collapses
    any number of configuration sources into a single tree of
    parameters.
    """
    delim = '.'
    path_factory = ParameterPath
    coerce_factories = {
            # {TYPE: FACTORY}
            bool: Boolean,
            type(None): lambda x: x,
    }

    def __init__(self, name, default=None, help="", coerce=None,
            parent=None, **kwargs):
        if isinstance(name, Parameter):
            self = name
        else:
            self.name = name
            self.default = default
            self.coerce = coerce
            self.help = help
            self.data = {}
            self.raw_value = Nothing

        for k, v in kwargs.items():
            setattr(self, k, v)

        self.parent = parent

    def __iter__(self):
        """Iterate on children, not data itself."""
        return iter(self.children)

    def __str__(self):
        return "<Parameter %s/%s>" % (self.path, self.value)

    def __repr__(self):
        return "Parameter(name=%s, default=%s, help=%s, parent=%s)" % (
                self.name, self.default, self.help, self.parent)

    def get_value(self):
        """Get the "coerced" value of the Parameter.

        If an explicit coercion method was supplied, use it. If none
        was supplied, use the type of the .default attribute to find
        it in the .coerce_factories attribute. If no value has been
        set, simply return the (uncoerced) default value.
        """
        value = self.default
        if self.raw_value is not Nothing:
            value = self.raw_value

            coerce = self.coerce
            if coerce is None:
                key = type(self.default)
                if key not in self.coerce_factories:
                    key = type(None)
                coerce = self.coerce_factories[key]
            value = coerce(value)

        return value

    value = property(fget=get_value,
            fset=lambda self, new: setattr(self, "raw_value", new),
            doc="""Provide a coerced version of .raw_value.""")
    del(get_value)

    @property
    def path(self):
        parent = getattr(self.parent, "path", None)
        if parent is not None:
            path = parent + [self,]
        else:
            path = []

        return self.path_factory(path)

    @property
    def children(self):
        children = []
        for child in self.data.values():
            children.append(child)
            children.extend(child.children)
        return children

    def add(self, parameter, *args, **kwargs):
        """Add a parameter.

        If 'parameter' is not a Parameter instance, a new parameter
        will be created with that name (and the other arguments). If
        'parameter' is a Parameter instance, it will be added (and
        the other arguments will be ignored). The child can be
        accessed as an attribute of the parent. This allows access
        to children as follows:

            >>> foo = Parameter("foo")
            >>> foo.add("bar")
            >>> foo.bar
        """
        if not isinstance(parameter, Parameter):
            cls = type(self)
            parameter = cls(parameter, *args, **kwargs)

        parameter.parent = self

        # Always update self.data -- this is the One True register
        # of children.
        self.data[parameter.name] = parameter

    def remove(self, parameter):
        """Remove a parameter.

        If 'parameter' is a Parameter instance, its 'name' attribute
        will be used to find the correct parameter to remove.
        Otherwise, the parameter with the name 'parameter' will be
        removed. In both cases, the parameter will no longer be
        accessible as an attribute of the parent.
        """
        name = getattr(parameter, 'name', parameter)

        # Clean up self.data
        self.data.pop(name)

class ParameterHandler(object):
    """Handle application parameters.

    The ParameterHandler interfaces between the abstract parameters
    defined by an application and the actual source of configuration
    information. This source may be the run-time arguments passed to
    the application (sys.argv), the execution environment
    (os.environ) or even a configuration file. 
    
    In each case, the Handler interprets the source according to the
    Parameters it's been given.
    """

    def __init__(self, app, source):
        self.app = app
        self.source = source

    def handle(self, app, parameters):
        for parameter in parameters:
            self.handle_parameter(parameter)

            # Recurse into children if present.
            if parameter.children:
                self.handle(app, parameter.children)

    def handle_parameter(self, parameter):
        raise NotImplementedError

class EnvironParameterHandler(ParameterHandler):
    delim = '_'

    def __init__(self, environ):
        self.environ = environ or os.environ

    def get_param_name(self, parameter):
        """Convert parameter name to something useful. 
       
        foo.bar.baz -> FOO_BAR_BAZ
        """
        name = getattr(parameter, "var_name", None)

        if name is None:
            name = str(parameter.path).replace(parameter.delim, self.delim).upper()

        return name

    def handle_parameter(self, parameter):
        name = self.get_param_name(parameter)
        value = self.environ.get(name, None)
        if value is not None:
            parameter.value = value

class CLIParameterHandler(ParameterHandler):
    delim = '-'
    cmp = staticmethod(lambda x, y: \
            cmp(getattr(x, "short", x.name), getattr(y, "short", y.name)))
    parser_factory = optparse.OptionParser

    def __init__(self, argv):
        self.argv = argv

    def handle(self, app, parameters):
        self.parser = self.parser_factory(
                usage=app.usage,
                version=app.version,
                description=app.description,
                )
        self.parser.process_default_values = False

        # XXX: we'll need to map option names to parameters here...
        param_map = {}
        if self.cmp:
            parameters = sorted(parameters, self.cmp)
        for parameter in parameters:
            name = self.handle_parameter(parameter)
            param_map[name] = parameter

            # Recurse into children if present.
            if parameter.children:
                self.handle(app, parameter.children)

        # Parse argv.
        opts, args = self.parser.parse_args(self.argv)

        # Update the parameter tree.

        # XXX: Unfortunately, there doesn't appear to be a nicer way
        # to do this. optparse falls back on __dict__ in this case,
        # too...
        for name, opt in vars(opts).items():
            if opt is not Default:
                parameter = param_map[name]
                parameter.value = opt

        # Set the application's args attribute.
        app.args = args

    def handle_parameter(self, parameter):
        option_attrs = optparse.Option.ATTRS
        name = str(parameter.path).replace(parameter.delim, self.delim)
        short = getattr(parameter, "short", "-%s" % name[0])
        long = getattr(parameter, "long", "--%s" % name)
        kwargs = dict((k, v) for k, v in vars(parameter).items() \
                if k in option_attrs)
        kwargs["dest"] = kwargs.get("dest", name)

        # Set a default sentinel since the parameter itself knows
        # what the default is. Otherwise, we can't decide later
        # whether to use the parameter's default or the option's
        # value.
        kwargs["default"] = Default
        
        self.parser.add_option(short, long, **kwargs)
        
        return name

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
        logging.setLoggerClass(CLILogger)
        self.log = logging.getLogger(self.name)

        # Create formatters.
        message_formatter = Formatter(self.message_format)
        date_formatter = Formatter(self.date_format)
        verbose_formatter = Formatter()
        self.formatter = message_formatter

        self.log.setLevel(self.log.default_level)

    def pre_run(self):
        """Configure logging before running the app."""
        super(LoggingApp, self).pre_run()
        self.log.setLevel(opts=self.params)

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
        self.add_param("daemonize", False, "run the application in the background", 
                action="store_true")
        self.add_param("user", None, "change to USER[:GROUP] after daemonizing")
        self.add_param("pidfile", None, "write PID to PIDFILE after daemonizing")
        self.add_param("logfile", None, "write logs to LOGFILE")

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

        if self.params.pidfile:
            self.log.debug("Writing pidfile %s", self.params.pidfile)
            pidfile = open(self.params.pidfile, 'w')
            pidfile.write('%i\n' % os.getpid())
            pidfile.close()

        if self.params.user:
            import grp
            import pwd
            delim = ':'
            user, sep, group = self.params.user.partition(delim)

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
