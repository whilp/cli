from distutils.cmd import Command

try:
	from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()

from lib import __name__, __version__, __description__, \
    __author__, __author_email__, __url__

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
    "name": __name__,
    "version": __version__,
    "description": __description__,
    "author": __author__,
    "author_email": __author_email__,
    "url": __url__,
    "package_dir": {__name__: "lib"},
    "cmdclass": {"test": test},
}

setup(**setup_options)
