import os
import sys
import unittest

from glob import glob

_import = lambda m: __import__(os.path.basename(os.path.splitext(m)[0]))

def issubclass(C, B):
    if C == B:
        return False
    try:
        return __builtins__.issubclass(C, B)
    except TypeError:
        return False

test_dir = os.path.abspath(os.path.dirname(__file__))
test_modules = glob(os.path.join(test_dir, "test_*.py")

sys.path.insert(0, test_dir)
test_modules = [_import(x) for x in test_modules]

def run_tests():
    tests = []
    for module in test_modules:
        for name, obj in vars(module).items():
            if issubclass(obj, unittest.TestCase):
                tests.append(unittest.defaultTestLoader.loadTestsFromTestCase(obj))
    unittest.TextTestRunner(verbosity=2).run(unittest.TestSuite(tests))

if __name__ == "__main__":
    run_tests()
