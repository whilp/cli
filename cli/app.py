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


__all__ = ["App", "EnvironParameterHandler", "CLIParameterHandler",
        "CommandLineApp", "LoggingApp"]

Nothing = object()

def plural(number):
    """Return 's' if number is != 1."""
    return number != 1 and 's' or ''

def Boolean(thing):
    """Decide if 'thing' is True or False.

    If thing is a string, convert it to lower case and, if it starts
    with 'y' or 't' (as in 'yes' or 'true'), return True. If it
    starts with some other character, return False. Otherwise,
    return True if 'thing' is True (in the Pythonic sense).
    """
    if callable(getattr(thing, 'lower', None)):
        thing = thing.lower()
        if thing[0] in 'yt':
            return True
        else:
            return False
    elif thing:
        return True
    else:
        return False

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

class AttributeDict(UserDict, object):
    """A dict that maps its keys to attributes."""

    def __getattribute__(self, attr):
        """Fetch an attribute.

        If the instance has the requested attribute, return it. If
        not, look for the attribute in the .data dict. If the
        requested attribute can't be found in either location, raise
        AttributeError.
        """
        try:
            value = super(AttributeDict, self).__getattribute__(attr)
        except AttributeError:
            data = super(AttributeDict, self).__getattribute__("data")
            value = data.get(attr, Nothing)
            if value is Nothing:
                raise

        return value

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
        return self.data.values()

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
            parameter = Parameter(parameter, *args, **kwargs)

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

    def handle(self, parameters):
        for parameter in parameters:
            self.handle_parameter(parameter)

            # Recurse into children if present.
            if parameter.children:
                self.handle(parameter.children)

    def handle_parameter(self, parameter):
        raise NotImplementedError

class EnvironParameterHandler(ParameterHandler):
    delim = '_'

    def __init__(self, app, environ):
        self.app = app
        self.environ = environ

    def handle_parameter(self, parameter):
        # Convert parameter name to something useful. 
        # foo.bar.baz -> FOO_BAR_BAZ
        name = str(parameter.path).replace(parameter.delim, self.delim).upper()

        value = self.environ.get(name, None)
        if value is not None:
            parameter.value = value

class CLIParameterHandler(ParameterHandler):
    delim = '-'

    def __init__(self, app, argv):
        self.app = app
        self.argv = argv
        self.parser = optparse.OptionParser(
                usage=self.app.usage,
                version='',     # XXX: this would be nice
                description='', # same here
                epilog='',      # and here
                )

    def handle(self, parameters):
        # XXX: we'll need to map option names to parameters here...
        param_map = {}
        for parameter in parameters:
            name = self.handle_parameter(parameter)
            param_map[name] = parameter

            # Recurse into children if present.
            if parameter.children:
                self.handle(parameter.children)

        # Parse argv.
        opts, args = self.parser.parse_args(self.argv)

        # Update the parameter tree.

        # XXX: Unfortunately, there doesn't appear to be a nicer way
        # to do this. optparse falls back on __dict__ in this case,
        # too...
        for name, opt in vars(opts).items():
            parameter = param_map[name]
            parameter.value = opt

        # Set the application's args attribute.
        self.app.args = args

    def handle_parameter(self, parameter):
        option_attrs = optparse.Option.ATTRS
        name = str(parameter.path).replace(parameter.delim, self.delim)
        short = "-%s" % name[0]
        long = "--%s" % name
        kwargs = dict((k, v) for k, v in vars(parameter).items() \
                if k in option_attrs)
        
        self.parser.add_option(short, long, **kwargs)
        
        return name

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

    def __init__(self, main, config_file=None, argv=None, env={},
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
        self.args = []

        self.params = self.param_factory("root")
        self.param_handlers = []

        self.setup()

    def setup(self):
        # Set up param handlers.
        environ_handler = EnvironParameterHandler(self, self.env)
        cli_handler = CLIParameterHandler(self, self.argv)

        self.param_handlers.append(environ_handler)
        self.param_handlers.append(cli_handler)

    @property
    def name(self):
        return getattr(self.main, 'func_name', self.main.__class__.__name__)

    def add_param(self, *args, **kwargs):
        """Add a parameter."""
        self.params.add(*args, **kwargs)

    def handle_parameters(self):
        """Apply each handler to the list of parameters.

        Each handler should define a .handle() method which takes as
        its single argument a list of Parameter objects. It should
        attempt to find a value for each parameter in its source and
        update the parameter objects accordingly. Once all parameter
        handlers have been run, replace all leaves in the parameter
        tree with their values.
        """
        for handler in self.param_handlers:
            handler.handle(self.params)

        self.resolve_parameters(self.params)

    def resolve_parameters(self, parameters):
        """Walk the parameter tree, replacing leaves with their values.

        Parameters that aren't leaves will remain untouched.
        In cases where a parameter's name is the same as an
        attribute of its parent (for example, 'keys'), the parent's
        attribute will be overridden.
        """
        for parameter in parameters:
            if parameter.children:
                self.resolve_parameters(parameter.children)
            else:
                self.resolve_parameter(parameter)

    def resolve_parameter(self, parameter):
        """Replace the parameter in the tree with its value."""
        path = [x.name for x in parameter.path]
        parent = self.params
        for node in path[:-1]:
            parent = getattr(parent, node.name)
        setattr(parent, parameter.name, parameter.value)

    @property
    def usage(self):
        return '%prog ' + (self.main.__doc__ or '')

    def pre_run(self):
        """Perform actions before .main() is run."""
        # Update parameters.
        self.handle_parameters()

    def post_run(self, returned):
        """Perform actions after .main() is run."""
        if self.exit_after_main:
            sys.exit(returned)
        else:
            return returned

    def run(self):
        """Run the application's callable.

        If the callable hasn't already been determined, discover it
        and pass it the resolved options, arguments and Application
        object. If the App.exit_after_main is True, call sys.exit()
        with the return value of the application's callable.
        Otherwise, return the result.

        This behavior can be customized by redefining the
        {pre,post}_run methods.
        """
        self.pre_run()

        returned = self.main(self, *self.args)

        return self.post_run(returned)

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
        super(LoggingApp, self).setup()

        # Add logging-related options.
        self.add_param("verbose", 0, "raise the verbosity",
                action="count")
        self.add_param("quiet", 0, "decrease the verbosity",
                action="count")
        self.add_param("silent", False, "only log warnings",
                action="store_true")

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
        """Configure logging before running the app."""
        super(LoggingApp, self).pre_run()
        self.log.setLevel(opts=self.params)

def test(app, *args):
    pass

App = LoggingApp

if __name__ == "__main__":
    from test import test
    app = App(test)
    app.run()