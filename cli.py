import logging
import optparse
import sys

from ConfigParser import ConfigParser
from UserDict import UserDict
from inspect import getargs
from logging import Formatter, StreamHandler
from operator import itemgetter, attrgetter
from string import letters

"""
Copyright (c) 2008 Will Maier <will@m.aier.us>

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

VALUE_CHARACTERS = letters + "-_"

def fmt_arg(arg):
    """Return 'arg' formatted as a standard option name."""
    return arg.lstrip('-').replace('_', '-')

class Error(Exception):
    pass

class MainError(Error):
    pass

class ParameterError(Error):
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

        level = self.default_level + (10 * (opts.quiet - opts.verbose))

        if opts.silent:
            level = self.silent_level
        elif level <= logging.NOTSET:
            level = logging.DEBUG

        self.level = level

class Values(optparse.Values, UserDict):
    delim = '.'
    args = []

    def __getattr__(self, key):
        try:
            return self.__dict__[key]
        except KeyError:
            return self[key]

    @property
    def data(self):
        return self.__dict__

    def set(self, name, value):
        """Set option 'name' to 'value'.

        Options with delimiter characters in their names represent
        options several levels down in the Values tree. Create as
        many Values instances as necessary before setting the leaf
        instance to 'value'.
        """
        subnames = name.split(self.delim)
        name = subnames.pop()
        parent = self

        # Build the Values tree.
        for n in subnames:
            if not hasattr(parent, n):
                setattr(parent, n, self.__class__())
            parent = getattr(parent, n)

        parent._update_loose({name: value})

class Parameter(object):

    def __init__(self, name, default=None, help=""):
        if isinstance(name, Parameter):
            self = name
        else:
            self.name = name
            self.default = default
            self.help = help

    @property
    def children(self):
        return [v for k, v in vars(self).items() if isinstance(v, Parameter)]

    def add(self, parameter, default=None, help=""):
        """Add a parameter.

        If 'parameter' is not a Parameter instance, a new parameter
        will be created with that name (and the other arguments). If
        'parameter' is a Parameter instance, it will be added (and
        the other arguments will be ignored). In any case, if the
        object to be added already exists and is not a Parameter
        instance, add() will raise ParameterError.
        """
        if not isinstance(parameter, Parameter):
            parameter = Parameter(parameter, default, help)

        try:
            self.remove(parameter)
        except ParameterError:
            raise ParameterError("Can't overwrite non-Parameter "
                    "child '%s'" % parameter.name)

        setattr(self, parameter.name, parameter)

    def remove(self, parameter):
        """Remove a parameter.

        If 'parameter' is a Parameter instance, its 'name' attribute
        will be used to find the correct parameter to remove.
        Otherwise, the parameter with the name 'parameter' will be
        removed. If the object to be removed isn't a Parameter
        instance, remove() will raise ParameterError.
        """
        Nothing = object()
        name = getattr(parameter, 'name', parameter)
        current = getattr(self, name, Nothing)

        if isinstance(current, Parameter):
            delattr(self, name)
        elif current is Nothing:
            pass
        else:
            raise ParameterError("Can't remove non-Parameter child "
                    "'%s'" % name)

class CommandLineApp(object):
    """A command-line application.

    Command-line applications (CLI apps) perform a task based in
    part on options and arguments passed on the command line. The
    App object makes it easy to develop simple CLI apps.

    Instantiated CLI apps parse options, arguments and (optionally)
    other configuration information and pass them to a single
    callable. This callable must support the App interface, which
    means its signature should be something like the following:

        def main(opts, args, app):

    Whether or not the callable actually _uses_ any of this
    information is optional, though it must accept them.
    """
    optparser_factory = optparse.OptionParser
    param_factory = Parameter

    def __init__(self, main, config_file=None, argv=None, env=None,
            exit_after_main=True, stdin=None, stdout=None,
            stderr=None):
        self.main = main
        self.config_file = config_file
        self.argv = argv
        self.env = env
        self.exit_after_main = exit_after_main
        self.stdin = stdin and stdin or sys.stdin
        self.stdout = stdout and stdout or sys.stdout
        self.stderr = stderr and stderr or sys.stderr

        self.params = self.param_factory("root")

        try:
            self.setup()
        except NotImplementedError:
            pass

    def setup(self):
        raise NotImplementedError

    @property
    def name(self):
        return getattr(self.main, 'func_name', self.main.__class__.__name__)

    def add_param(self, name, default=None, help=''):
        """Add a parameter."""
        self.params.append(name, default, help)

    @property
    def args(self):
        raise NotImplementedError

    @property
    def usage(self):
        return '%prog ' + (self.main.__doc__ or '')

    def run(self):
        """Run the application's callable.

        If the callable hasn't already been determined, discover it
        and pass it the resolved options, arguments and Application
        object. If the App.exit_after_main is True, call sys.exit()
        with the return value of the application's callable.
        Otherwise, return the result.
        """
        returned = self.main(self, *self.args, **self.opts)

        if self.exit_after_main:
            sys.exit(returned)
        else:
            return returned

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

    def __init__(self, main, stream=None, logfile=None,
            message_format="%(message)s", 
            date_format="%(asctime)s %(message)s", **kwargs):
        self.logfile = logfile
        self.stream = stream
        self.message_format = message_format
        self.date_format = date_format
        super(LoggingApp, self).__init__(main, **kwargs)

    def setup(self):
        # Add logging-related options.
        self.add_option("verbose", 0, "raise the verbosity", "count")
        self.add_option("quiet", 0, "decrease the verbosity", "count")
        self.add_option("silent", False, "only log warnings", "store_true")

        # Create logger.
        logging.setLoggerClass(CLILogger)
        self.log = logging.getLogger(self.name)
        
        # Create handlers.
        stream_handler = StreamHandler(self.stream)
        handler = stream_handler
        if self.logfile is not None:
            file_handler = FileHandler(self.logfile)
            handler = file_handler

        # Create formatters.
        message_formatter = Formatter(self.message_format)
        date_formatter = Formatter(self.date_format)
        verbose_formatter = Formatter()
        formatter = message_formatter

        handler.setFormatter(formatter)
        self.log.setLevel(self.log.default_level)
        self.log.addHandler(handler)

    def run(self):
        """Run the app.

        Before running, set the logger's verbosity level based on
        the CLI options.
        """
        self.log.setLevel(opts=self.values[0])
        super(LoggingApp, self).run()

App = LoggingApp

if __name__ == "__main__":
    def test_app(app, *args, **kwargs):
        """[options] foo

        this is a test.
        """
        print args
        print kwargs
        print "test"

    app = App(test_app)
    app.run()
