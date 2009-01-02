import sys

from ConfigParser import ConfigParser
from inspect import getargs
from optparse import OptionParser, Values

class Error(Exception):
    pass

class MainError(Error):
    pass

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

    def __init__(self, main=None, config_file=None, argv=None,
            exit_after_main=True):
        self.main = main
        self.config_file = config_file
        self.argv = argv
        self.exit_after_main = exit_after_main

    def parse_config(self, config_file):
        """Parse the configuration file.
        
        Returns a single Values instance representing the
        configuration file.
        """
        if config_file is None:
            return Values()

        # XXX: seed the parser with defaults here?
        parser = ConfigParser()
        parser.read(config_file)

    def parse_env(self):
        """Parse the execution environment."""
        pass

    def parse_cli(self):
        """Parse CLI options and arguments.

        Returns a tuple: (opts, args). 
        """
        parser = OptionParser(self.usage)
        # add options here.

        opts, args = parser.parse_args(self.argv)

        return opts, args

    def parse_options(self):
        """Parse all application options.

        In addition to the standard CLI options and arguments, this
        also includes environment variables and configuration file
        directives which are resolved to options and arguments.
        Options specified in more than one of the above sources are
        resolved in the following order, with the rightmost source
        winning:

            configuration -> environment -> CLI

        Returns a tuple (opts, args).
        """
        opts = self.parse_config(self.config_file)
        eopts = self.parse_env()
        copts, cargs = self.parse_cli()

        # XXX: hook these in when the Values instances know about
        # updates.
        #opts.update(eopts)
        #opts.update(copts)

        return opts, cargs

    @property
    def opts(self):
        return self.parse_options()[0]

    @property
    def args(self):
        return self.parse_options()[1]

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

        if len(args) != 3 or (varargs or varkw):
            raise MainError("main() must take three arguments or varargs/varkw")

        return main

    def run(self):
        """Run the application's callable.

        If the callable hasn't already been determined, discover it
        and pass it the resolved options, arguments and Application
        object. If the App.exit_after_main is True, call sys.exit()
        with the return value of the application's callable.
        Otherwise, return the result.
        """
        main = self.find_main(self.main)

        returned = main(self.opts, self.args, self)

        if self.exit_after_main:
            sys.exit(returned)
        else:
            return returned

def main(opts, args, app=None):
    print 'cli.App test!'

if __name__ == '__main__':
    app = App(config_file='sample.config')

    app.run()
