import os
from distutils.core import Command, setup

import cli

class TestCommand(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from cli import App
        from cli.test import test
        app = App(test, argv=[os.getcwd()])
        app.params.verbose.default = self.verbose
        app.run()

docs = [os.path.join('docs', x) for x in os.listdir('docs')]
examples = docs = [os.path.join('examples', x) for x in os.listdir('examples')]

setup(name="CLI",
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
        py_modules=['cli'],
        cmdclass = {"test": TestCommand})
