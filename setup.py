import os
from distutils.core import setup

import cli
from cli.test import TestCommand

docs = [os.path.join('docs', x) for x in os.listdir('docs')]
examples = docs = [os.path.join('examples', x) for x in os.listdir('examples')]

setup(name="pyCLI",
        version=cli.__version__,
        description="Simple, Object-Oriented approach to Python CLI apps",
        author="Will Maier",
        author_email="will@m.aier.us",
        url="http://code.lfod.us/cli",
        license=cli.__license__,
        packages=["cli"],
        data_files=[
            ('share/doc/py-cli/', docs),
            ('share/examples/py-cli/', examples)],
        cmdclass = {"test": TestCommand})
