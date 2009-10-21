import os
import sys

from glob import glob

__all__ = ["Queue", "foo", "spam"]
compat_dir = os.path.abspath(os.path.dirname(__file__))

for name in __all__:
    try:
        module = __import__(name)
    except ImportError:
        sys.path.insert(0, compat_dir)
        module = __import__(name)
        sys.path.pop(0)
    locals()[name] = module

del(glob, os, sys, compat_dir, name, module)
