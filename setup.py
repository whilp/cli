import os

from distutils.cmd import Command
from distutils.command.install import INSTALL_SCHEMES

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()

from lib import __package_name__, __version__, __description__, \
    __author__, __author_email__, __url__, __license__, \
    __long_description__

class test(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        import tests
        tests.run_tests()

setup_options = {
    "name": __package_name__,
    "version": __version__,
    "description": __description__,
    "long_description": __long_description__,
    "author": __author__,
    "author_email": __author_email__,
    "url": __url__,
    "package_dir": {__package_name__: "lib"},
    "license": __license__,
    "cmdclass": {"test": test},
}

setup(**setup_options)
