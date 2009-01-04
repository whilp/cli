import logging
import optparse
import sys

from ConfigParser import ConfigParser
from inspect import getargs
from logging import Formatter, StreamHandler
from optparse import Option, OptionParser

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

class Values(optparse.Values):
    delim = '.'
    args = []

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

    def update_from_config(self, config_file):
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
        # XXX: seed the parser with defaults here?
        parser = ConfigParser()
        parser.read(config_file)

        for section in parser.sections():
            for option in parser.options(section):
                name = self.delim.join((section, option))
                value = parser.get(section, option)
                # XXX: hook in vars here?
                self.set(name, value)

    def update_from_env(self, env):
        """Parse 'env' and update the Values tree.

        'env' should be a dictionary similar to that provided by
        os.environ. Keys will be converted from 'FOO_BAR' notation
        to 'foo.bar'; values will be untouched.
        """
        for key, value in env.items():
            key = self.delim.join(key.lower().split('_'))
            self.set(key, value)

    def update_from_cli(self, parser, argv):
        """Parse the command line an update the Values tree.

        'parser' should be an instance of optparse.OptionParser;
        argv should be (in most cases) sys.argv.
        """
        opts, self.args = parser.parse_args(argv)

        # XXX: Is there a nicer way of discovering the options and
        # their names? optparse looks at __dict__ directly, too, so
        # this may be As Good As It Gets.
        for name, opt in opts.__dict__.items():
            self.set(name, opt)

class App(object):
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
    optparser_factory = OptionParser

    def __init__(self, name, main=None, config_file=None, argv=None,
            env=None, exit_after_main=True):
        self.name = name
        self.main = self.find_main(main)
        self.config_file = config_file
        self.argv = argv
        self.env = env
        self.exit_after_main = exit_after_main

        self.parser = self.optparser_factory(self.usage or None)

        setup = getattr(self, 'setup')
        if callable(setup):
            setup()

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
        """Parse all application options.

        In addition to the standard CLI options and arguments, this
        also includes environment variables and configuration file
        directives which are resolved to options and arguments.
        Options specified in more than one of the above sources are
        resolved in the following order, with the rightmost source
        winning:

            configuration -> environment -> CLI
        """
        values = self.values_factory()

        if self.config_file is not None:
            values.update_from_config(self.config_file)
        if self.env is not None:
            # Filter env for variables starting with our name. A
            # mapping like {'OURAPP_FOO_BAR': 'foo'} will become
            # {'FOO_BAR': 'foo'}.
            env = dict([('_'.join(k.split('_')[1:]), v) \
                    for k, v in self.env.items() \
                    if k.lower().startswith(self.name.lower() + '_')])
            values.update_from_env(env)

        values.update_from_cli(self.parser, self.argv)

        return values

    @property
    def opts(self):
        return self.values.__dict__

    @property
    def args(self):
        return self.values.args

    @property
    def usage(self):
        return self.main.__doc__ or ''

    def find_main(self, main=None):
        """Find a suitable main() callable.

        If the supplied 'main' argument is not a callable, search
        globals() for a suitable callable. If no callable is found
        or the chosen callable doesn't support the App interface
        (see cli.App.__doc__ for more information), raise MainError.
        """
        if not callable(main):
            main = globals().get('main', None)

        if not callable(main):
            raise MainError("Could not find main()")

        args, varargs, varkw = getargs(main.func_code)

        return main

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

class LoggingApp(App):
    """A command-line application that knows how to log.

    A LoggingApp provides a 'log' attribute, which is a logger (from
    the logging module). The logger's verbosity is controlled via
    handy options ('verbose', 'quiet', 'silent') and sends its
    output to stderr by default (though it will log to a file if the
    'logfile' attribute is not None). Non-stderr streams can be
    requested by setting the 'stream' attribute to something besides
    None.
    """
    message_format = "%(message)s"
    date_format = "%(asctime)s %(message)s"

    def __init__(self, name, stream=None, logfile=None, **kwargs):
        self.logfile = logfile
        self.stream = stream
        super(LoggingApp, self).__init__(name, **kwargs)

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
        self.log.setLevel(opts=self.values)
        super(LoggingApp, self).run()

def main(app, *args, **kwargs):
    """docstring test."""
    log = app.log
    log.critical("critical")
    log.warning("warning")
    log.info("info")
    log.debug("debug")

if __name__ == '__main__':
    app = LoggingApp('ourapp')

    app.add_option('foo_test', False, "test help doc", "store_true")
    app.add_option('foo_test2', False, "test help doc", "store_true")

    app.run()
