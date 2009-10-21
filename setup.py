import os

from distutils.command.install import INSTALL_SCHEMES

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import cli
from cli.test import TestCommand

docs = [os.path.join('docs', x) for x in os.listdir('docs')]
examples = docs = [os.path.join('examples', x) for x in os.listdir('examples')]
tests = docs = [os.path.join('tests', x) for x in os.listdir('tests')]

for scheme in INSTALL_SCHEMES.values():
    scheme['data'] = scheme['purelib']

setup(name="pyCLI",
        version=cli.__version__,
        description="Simple, Object-Oriented approach to Python CLI apps",
        author="Will Maier",
        author_email="will@m.aier.us",
        url="http://code.lfod.us/cli",
        license=cli.__license__,
        packages=["cli"],
        data_files=[
            ('docs', docs),
            ('examples', examples),
            ('tests', tests)],
        cmdclass = {"test": TestCommand})
