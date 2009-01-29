import unittest

from inspect import isclass, isfunction

suite = unittest.TestSuite()
loader = unittest.TestLoader()

for name, obj in locals().items():
    class TestCase(unittest.TestCase):
        # XXX: fix class naming.

        @staticmethod
        def wrap_function(testcase, function):
            name = function.func_name
            doc = function.__doc__

            setattr(testcase, name, staticmethod(function))

        @staticmethod
        def wrap_class(testcase, cls):
            noop = lambda s: None
            setup_method = getattr(cls, "setup_method", noop)
            setUp = getattr(cls, "setUp", noop)
            teardown_method = getattr(cls, "teardown_method", noop)
            tearDown = getattr(cls, "tearDown", noop)

            tests = [(n, m) for n, m in vars(cls).items() if \
                    n.startswith("test_")]

            for name, method in tests:
                def wrapped_method(self):

                    method()

    if name.startswith("test_") and isfunction(obj):
        TestCase.wrap_function(TestCase, obj)
    elif name.startswith("Test") and isclass(obj):
        if issubclass(unittest.TestCase, obj):
            TestCase = obj
        else:
            #TestCase.something()
            pass
    suite.addTests(loader.loadTestsFromTestCase(TestCase))
unittest.TextTestRunner(verbosity=2).run(suite)
