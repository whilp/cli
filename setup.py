try:
    import setuptools
except ImportError:
    from distribute_setup import use_setuptools
    use_setuptools()
from setuptools import setup, find_packages

try:
    from distutils.command.build_py import build_py_2to3 as build_py
except ImportError:
    from distutils.command.build_py import build_py

import sys, os

libdir = "lib"

sys.path.insert(0, libdir)

import cli as pkg

setup_options = {
    "name": pkg.__project__,
    "version": pkg.__version__,
    "description": pkg.__description__,
    "long_description": pkg.__doc__,
    "classifiers": pkg.__classifiers__,
    "keywords": pkg.__keywords__,
    "author": pkg.__author__,
    "author_email": pkg.__author_email__,
    "url": pkg.__url__,
    "packages": find_packages(libdir),
    "package_dir": {"": libdir},
    "include_package_data": True,
    "zip_safe": False,
    "install_requires": pkg.__requires__,
    "entry_points": """
        # -*- Entry points: -*-
    """,
    "test_suite": "cli.tests",
    "cmdclass": { "build_py": build_py },
}

setup(**setup_options)
