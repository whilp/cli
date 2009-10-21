import os

from distutils.cmd import Command

try:
    from setuptools import setup
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()

from lib import __package_name__, __package__, __version__, \
    __description__, __author__, __author_email__, __url__, \
    __license__, __long_description__

class test(Command):
    user_options = []

    def initialize_options(self):
        pass

    def finalize_options(self):
        pass

    def run(self):
        from lib import tests
        tests.run_tests()

def split(path):
    head, tail = os.path.split(path)
    if not head:
        return [tail]
    elif not tail:
        return [head]
    else:
        return split(head) + [tail]

# Compile the list of packages available, because distutils doesn't have
# an easy way to do this. Loosely lifted from Django.
root_dir = os.path.dirname(__file__)
if root_dir != '':
    os.chdir(root_dir)

def find(root, ignore='.'):
    for dirpath, dirnames, filenames in os.walk(root):
        for i, dirname in enumerate(dirnames):
            if dirname.startswith(ignore): dirnames.pop(i)
        for filename in filenames:
            yield os.path.join(dirpath, filename)

def find_packages(root):
    for filename in find(root):
        pieces = split(filename)
        if pieces.pop(-1) == "__init__.py":
            yield '.'.join(pieces)
    
setup_options = {
    "name": __package_name__,
    "version": __version__,
    "description": __description__,
    "long_description": __long_description__,
    "author": __author__,
    "author_email": __author_email__,
    "url": __url__,
    "packages": list(find_packages("lib")),
    "data_files": [("docs", list(find("docs"))), ("examples", list(find("examples")))],
    "package_dir": {__package__: "lib"},
    "license": __license__,
    "cmdclass": {"test": test},
}

setup(**setup_options)
