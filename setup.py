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

docs = [os.path.join('docs', x) for x in os.listdir('docs')]
examples = docs = [os.path.join('examples', x) for x in os.listdir('examples')]
tests = docs = [os.path.join('tests', x) for x in os.listdir('tests')]

setup_options = {
    "name": __package_name__,
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "author_email": __author_email__,
    "url": __url__,
    "license": __license__,
    "package_dir": {__package_name__: "lib"},
    "cmdclass": {"test": test},
}

setup(**setup_options)
