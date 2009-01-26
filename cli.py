import logging
import optparse
import sys

from ConfigParser import ConfigParser
from UserDict import UserDict
from inspect import getargs
from logging import Formatter, StreamHandler
from operator import itemgetter

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

class Error(Exception):
    pass

class MainError(Error):
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

class Value(object):
    option_factory = optparse.Option

    def __init__(self, name, default=None, help='', coerce=str, **kwargs):
        self.name = name
        self.default = default
        self.help = help
        self.coerce = coerce
        self.kwargs = kwargs

    @property
    def dest(self):
        return self.name.replace('-', '_')

    @property
    def short(self):
        return "-%s" % self.name[0]

class RawValue(UserDict):
    option_factory = optparse.Option

    def __init__(self, name, default, help, coerce=str,
            action="store"):
        data = locals().copy()
        data.pop('self')
        self.data = data

    @property
    def name(self):
        return self["name"].replace('_', '-')

    @property
    def short_flag(self):
        return self.get("short_flag", "-%s" % self.name[0])

    @property
    def long_flag(self):
        return self.get("long_flag", "--%s" % self.name)

    action = property(itemgetter("action"))
    default = property(itemgetter("default"))
    help = property(itemgetter("help"))

    @property
    def option(self):
        return self.option_factory(**self.data)

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
    values_factory = Values
    optparser_factory = optparse.OptionParser

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

        self.parser = self.optparser_factory(prog=self.name,
                usage=self.usage or None)

        self.raw_values = []
        self.values_handlers = [
            self.config_values_handler,
            self.env_values_handler,
            self.cli_values_handler]

        setup = getattr(self, 'setup', None)
        if callable(setup):
            setup()

    @property
    def name(self):
        return getattr(self.main, 'func_name', self.main.__class__.__name__)

    def add_option(self, name, default, help, action="store",
            **kwargs):
        """Add an option to the CLI option parser.
        
        The option names are generated from the 'name' argument. In
        most cases, the short option will become '-n', where 'n' is
        the first character of 'name'. If an option is already
        defined with this character, it will automatically be
        capitalized. The long form of the name will be 'name', with
        the '-' replaced by a '_' (if present).
        """
        short = kwargs.pop('short', '-%s' % name[0])

        if self.parser.has_option(short):
            short = '-%s' % short[-1].capitalize()

        self.parser.add_option(
            short,
            kwargs.pop('long', '--%s' % name.replace('_', '-')),
            dest = name,
            action = action,
            default = default,
            help = help,
            **kwargs)

    @property
    def values(self):
        """Parse and return all application options.

        When the values property is accessed, all registered values
        handlers will be run in sequence. Handlers that are called
        later in the sequence can overwrite values set by earlier
        handlers. By default, this produces a resolution order as
        follows (from earliest to latest):

            configuration 
            environment
            CLI

        In this case, values found on the command line will override
        identical values set in the application's environment or
        configuration files.

        Inheritors (or instances) may alter this order or remove the
        default handlers by manipulating the values_handlers
        attribute.
        """
        values = self.values_factory()
        for handler in self.values_handlers:
            handler(values)

        return values, values.args

    def config_values_handler(self, values):
        """Parse a configuration file and update the Values tree.

        The config file is read using ConfigParser.ConfigParser.
        All options are flattened into a single-level structure such
        that the following two options are equivalent:

            [one.two]
            three = four

            [one]
            two.three = four

        In each case, the value 'one.two.three' will equal 'four'.
        In cases where the same option name has multiple values, the
        last entry with that name will be used.
        """
        if self.config_file is None:
            return

        # XXX: seed the parser with defaults here?
        parser = ConfigParser()
        parser.read(self.config_file)

        for section in parser.sections():
            for option in parser.options(section):
                name = self.delim.join((section, option))
                value = parser.get(section, option)
                # XXX: hook in vars here?
                values.set(name, value)

    def env_values_handler(self, values):
        """Parse 'env' and update the Values tree.

        The 'env' attribute should be a dictionary similar to that
        provided by os.environ. Keys will be converted from
        'FOO_BAR' notation to 'foo.bar'; values will be untouched.
        """
        if self.env is None:
            return

        # Filter env for variables starting with our name. A
        # mapping like {'OURAPP_FOO_BAR': 'foo'} will become
        # {'FOO_BAR': 'foo'}.
        env = dict([('_'.join(k.split('_')[1:]), v) \
                for k, v in self.env.items() \
                if k.lower().startswith(self.name.lower() + '_')])

        for key, value in env.items():
            key = self.delim.join(key.lower().split('_'))
            values.set(key, value)

    def cli_values_handler(self, values):
        """Parse the command line and update the Values tree."""
        opts, args = self.parser.parse_args(self.argv)

        # XXX: Is there a nicer way of discovering the options and
        # their names? optparse looks at __dict__ directly, too, so
        # this may be As Good As It Gets.
        for name, opt in opts.__dict__.items():
            values.set(name, opt)

    @property
    def opts(self):
        return self.values[0].__dict__

    @property
    def args(self):
        return self.values[1]

    @property
    def usage(self):
        return '%prog ' + (self.main.__doc__ or '')

    def pre_run(self):
        """Perform any last-minute setup before .main() is called."""
        pass

    def run(self):
        """Run the application's callable.

        If the callable hasn't already been determined, discover it
        and pass it the resolved options, arguments and Application
        object. If the App.exit_after_main is True, call sys.exit()
        with the return value of the application's callable.
        Otherwise, return the result.
        """
        self.pre_run()
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

    def pre_run(self):
        """Run the app.

        Before running, set the logger's verbosity level based on
        the CLI options.
        """
        self.log.setLevel(opts=self.values[0])

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
