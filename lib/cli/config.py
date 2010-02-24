"""\
:mod:`cli.config` -- applications that read config files
--------------------------------------------------------

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

from cli.app import CommandLineApp
from cli.ext import argparse

__all__ = ["ConfigApp"]

class ConfigApp(CommandLineApp):
    """A command-line application that reads a configuration file.

    A :class:`ConfigApp` is a :class:`CommandLineApp` that optionally
    reads a configuration file on startup. This configuration file can
    be written in one of several formats and may define an additional
    set of default parameter values. Values defined on the command line
    override those in the config file. In addition to those supported by
    the standard :class:`Application` and :class:`CommandLineApp`,
    arguments are:

    *configfile* is a file-like object or a string representing a path
    to a configuration file. If *configfile* is None, no configuration
    file will be read.
    """
    configparsers = []
    """A list of registered config file parsers.

    Each entry in the list should be a two-item tuple::

        (name, parserfunc)

    The parsers will be called in order by :meth:`pre_run`.
    """
    config = None
    """A Namespace instance.

    :attr:`config` contains the parsed configuration file (if any).
    Its attributes map to the config file's sections. Its
    attributes' attributes and their values map to the keys and
    values of the sections, respectively.
    """

    def __init__(self, main=None, configfile=None, **kwargs):
        self.configfile = configfile
        super(ConfigApp, self).__init__(main, **kwargs)

    def setup(self):
        """Configure the :class:`ConfigApp`.

        This method adds the :option:`-f` parameter to the application.
        """
        super(ConfigApp, self).setup()

        # Add daemonizing options.
        configdefault = "no configuration file is read"
        if self.configfile is not None:
            configdefault = self.configfile
        self.add_param("-f", "--configfile", default=self.configfile,
            type=argparse.FileType(),
            help="open a configuration file (default: %s)" % configdefault)

    def pre_run(self):
        """Parse the configuration file and update the parameters.

        First, parse arguments on the command line (so that the user can
        specify an alternate configuration file). Then, call each of the
        registered parsers on the configuration file until it is
        successfully parsed (see :meth:`parseconfig`). If the parsed
        configuration file contains a *parameters* section, pass those
        values to the :class:`argparse.Action` instances created by
        :meth:`add_param`. Finally, update the config file
        parameters with the parameters found on the command line and
        then save the merged parameters as :attr:`params`.
        """
        super(ConfigApp, self).pre_run()

        if self.params.configfile is None:
            return

        parsed = self.parseconfig(self.params.configfile)
        if parsed is None:
            self.log.debug("Unable to parse config file")
            return

        self.config = parsed
        parameters = self.configparams(self.config)

        self.params = self.update_params(parameters, self.params)

    def parseconfig(self, config):
        """Parse a configuration file, returning a dictionary.

        Try each registered configuration parser (see
        :attr:`configparsers`) in order until one of them succeeds; return the
        resulting Namespace instance.
        """
        parsed = None
        for name, parser in self.configparsers:
            self.log.debug("Trying config parser %s")
            parsed = parser(config)
            if parsed is not None:
                self.log.debug("Config parser %s succeeded")
                break

        return parsed

    def configparams(self, config):
        """Extract parameter values from a parsed config file.

        *config* is a Namespace instance with a *parameters* attribute.
        For each action defined by :meth:`add_param` and saved in :attr:`actions`,
        check for an attribute on the *parameters* attribute with the
        same name. If it exists, its value is passed to the
        :class:`argparse.Action` instance. If the action is a
        :class:`argparse._CountAction`, the value should be a integer;
        for an interger *n*, the action will be called *n* times. For
        other actions, the value is passed directly to the action.
        """

        parameters = getattr(config, "parameters", None)
        if parameters is None:
            self.log.debug("No parameters defined in config file")
            return

        pns = argparser.Namespace()
        Nothing = object()
        for name, action in self.actions.items():
            values = getattr(parameters, name, Nothing)
            if values is Nothing:
                break

            if isinstance(action, argparse._CountAction):
                for i in range(int(values)):
                    action(self.argparser, pns, i)
            else:
                action(self.argparser, pns, values)

        return pns
