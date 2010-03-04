"""\
:mod:`cli.config` -- applications that read config files
--------------------------------------------------------

.. versionadded:: 1.0.2

The :mod:`cli.config` module provides an application that knows how to
read a variety of config file formats.
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

from ConfigParser import ConfigParser
from pprint import pprint

json = None
try:
    import json
except ImportError:
    try:
        import simplejson as json
    except ImportError:
        pass

from cli.log import LoggingApp
from cli.ext import argparse

__all__ = ["BaseParser", "ConfigApp", "IniConfigParser", "JSONConfigParser",
    "PythonConfigParser"]

class BaseParser(object):
    """Defines the parser API.

    Parsers must provide implementations for both :meth:`read` and
    :meth:`write`. Calls to either :meth:`read` or :meth:`write` should
    be idempotent; that is, they should not change the parser's overall
    state.

    All configuration files should include one or more sections. Each
    section may contain one or more key/value pairs. Some configuration
    parsers may support typed data or nested sections.

    If present, a :class:`ConfigApp` will examine the special "parameters"
    section and use it to find values for options not specified on the
    command line.
    """

    def read(self, config):
        """Read a configuration file.

        *config* is a file-like object with data in a format the
        parser understands. The parser calls the file-like object's
        :meth:`read` method, parses the contents and returns a
        dictionary representing the configuration.
        """
        raise NotImplementedError

    def write(self, config, buffer):
        """Serialize the provided configuration and write it out.

        *config* should be a dictionary with section names as its keys.
        Its values should also be dictionaries containing key/value
        pairs. *buffer* should be a file-like object. The parser will
        format the configuration dictionary and write it to the output
        buffer.
        """
        raise NotImplementedError

class IniConfigParser(BaseParser):
    """An .ini-style configuration file parser.

    The :class:`IniConfigParser` uses the standard
    :class:`ConfigParser.ConfigParser` to read and write its
    configuration files; see the ConfigParser documentation for a
    description of the format.

    .. note::

        :class:`ConfigParser.ConfigParser` values are always strings.
        This makes this parser unsuitable (without extension) for things
        like setting a default value for the verbose parameter (which
        must be an integer).
    """

    def read(self, config):
        parser = ConfigParser()
        parser.readfp(config)

        return dict((s, dict(parser.items(s))) for s in parser.sections())

    def write(self, config, buffer):
        parser = ConfigParser()
        for section, items in config.items():
            parser.add_section(section)
            for k, v in items.items():
                parser.set(section, k, v)

        parser.write(buffer)

class PythonConfigParser(BaseParser):
    """A Python configuration file parser.

    Python configuration files contain Python code that can be parsed by
    the interpreter's *exec* statement. The file must contain a series
    of dictionaries, each with any number of keys and values. For
    example::

        parameters = {
            "verbose": 3,
        }
        database = {
            "host": "localhost",
            "user": "admin",
        }
    """

    def read(self, config):
        _locals = {}
        exec config.read() in _locals

        return dict((k, v) for k, v in _locals.items() if not k.startswith("__"))

    def write(self, config, buffer):
        for k, items in config.items():
            buffer.write("%s = " % k)
            pprint(items, buffer)
            buffer.write('\n')

if json is not None:
    class JSONConfigParser(BaseParser):
        """A JSON configuration file parser.

        This parser reads configuration files written to conform to
        :rfc:`4627` using the :mod:`json` or :mod:`simplejson` modules.
        The root of the JSON document should be a dictionary with
        strings as its keys and other dictionaries as its values. For
        example::

            {
                "parameters": {"verbose": 3},
                "database": {"host": "localhost", "user": "admin"}
            }
        """
        
        def read(self, config):
            return json.load(config)

        def write(self, config, buffer):
            json.dump(config, buffer)

class ConfigApp(LoggingApp):
    """A command-line application that reads a configuration file.

    A :class:`ConfigApp` is a :class:`cli.log.LoggingApp` that
    optionally reads a configuration file on startup. This configuration
    file can be written in one of several formats and may define an
    additional set of default parameter values. Values defined on the
    command line override those in the config file. In addition to
    those supported by the standard :class:`cli.app.Application` and
    :class:`cli.log.LoggingApp`, arguments are:

    *configfile* is a file-like object or a string representing a path
    to a configuration file. If *configfile* is None, no configuration
    file will be read.
    """
    configparser_factory = IniConfigParser
    """A factory that produces configuration parsers.

    Usually, the factory will be a class that inherits from
    :class:`BaseParser`. It must override the :meth:`BaseParser.read`
    and :meth:`BaseParser.write` methods.
    """
    config = None
    """A Namespace instance.

    :attr:`config` contains the parsed configuration file (if any).
    Its attributes map to the config file's sections. Its
    attributes' attributes and their values map to the keys and
    values of the sections, respectively.
    """

    def __init__(self, main=None, configfile=None, configparser_factory=None, **kwargs):
        self.configfile = configfile
        if configparser_factory is not None:
            self.configparser_factory = configparser_factory
        super(ConfigApp, self).__init__(main, **kwargs)

    def setup(self):
        """Configure the :class:`ConfigApp`.

        This method adds the :option:`-f` parameter to the application.
        """
        super(ConfigApp, self).setup()
        self.configparser = self.configparser_factory()

        # Add config options.
        configdefault = "no configuration file is read"
        if self.configfile is not None:
            configdefault = self.configfile
        self.add_param("-f", "--configfile", default=self.configfile,
            type=argparse.FileType(),
            help="open a configuration file (default: %s)" % configdefault)

    def pre_run(self):
        """Parse the configuration file and update the parameters.

        First, parse arguments on the command line (so that the user
        can specify an alternate configuration file). Then, call the
        :attr:`configparser`'s :meth:`read` method on the config file.
        If the parsed configuration file contains a *parameters*
        section, pass those values to the :class:`argparse.Action`
        instances created by :meth:`cli.app.CommandLineApp.add_param`.
        Finally, update the config file parameters with the parameters
        found on the command line and then save the merged parameters as
        :attr:`cli.app.CommandLineApp.params`.
        """
        # Parse the command line so that the user can specify an
        # alternate config file. If we find a valid config file, we'll
        # end up doing this twice, so it's important that ConfigApp's
        # parents' pre_run() methods not have unexpected sideeffects.
        super(ConfigApp, self).pre_run()

        if self.params.configfile is None:
            return

        parsed = self.configparser.read(self.params.configfile)
        if parsed is None:
            self.log.debug("Unable to parse config file")
            return

        self.config = argparse.Namespace()
        # What follows is more or less Namespace's constructor. We do it
        # ourselves, though, because we otherwise get:
        #   TypeError: __init__() keywords must be strings
        # This occurs when the keys are unicode objects.
        for k, v in parsed.items():
            setattr(self.config, k, v)

        parameters = parsed.get("parameters", None)
        if parameters is None:
            self.log.debug("No parameters defined in config file")
            return

        # Update the default values of the existing actions. When we run
        # our parents' pre_run() method again, they'll pick up the new
        # defaults.
        for k, v in parameters.items():
            action = self.actions.get(k, None)
            if action is None:
                self.log.debug("No parameter matches default '%s' specified "
                    "parameters section of config file", k)
                continue

            action.default = v

        super(ConfigApp, self).pre_run()

    def configparams(self, parameters):
        """Extract parameter values from a parsed config file.

        *parameters* is a dictionary containing the keys and values from
        the parameters section of a config file. For each action
        defined by :meth:`add_param` and saved in :attr:`actions`,
        check for an If it exists, its value is passed to the
        :class:`argparse.Action` instance. If the action is a
        :class:`argparse._CountAction`, the value should be a integer;
        for an integer *n*, the action will be called *n* times. For
        other actions, the value is passed directly to the action.
        """

        pns = argparser.Namespace()
        Nothing = object()
        for name, action in self.actions.items():
            values = parameters.get(name, Nothing)
            if values is Nothing:
                break

            if isinstance(action, argparse._CountAction):
                for i in range(int(values)):
                    action(self.argparser, pns, i)
            else:
                action(self.argparser, pns, values)

        return pns
