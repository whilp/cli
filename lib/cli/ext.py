"""Includes:
    argparse - 2010.02.01
        LICENSE:    Apache License 2.0
        URL:        http://argparse.googlecode.com/svn/tags/r101/argparse.py
"""
import os

# Add included module names to __all__.
__all__ = ["argparse"]
project = os.path.basename(os.path.dirname(__file__))
ext = project + "._ext"

name, module = None, None
for name in __all__:
    try:
        module = __import__(name)
    except ImportError:
        module = __import__('.'.join((ext, name)), fromlist=[ext])
    locals()[name] = module

del(ext, module, name, project)
