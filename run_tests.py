import unittest

class TestFailed(Exception):
    pass

class BaseTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

def run_suite(suite):
    """Stolen from Python/Lib/test/test_support."""
    runner = unittest.TextTestRunner(sys.stdout, verbosity=2)

    result = runner.run(suite)
    if not result.wasSuccessful():
        if len(result.errors) == 1 and not result.failures:
            err = result.errors[0][1]
        elif len(result.failures) == 1 and not result.errors:
            err = result.failures[0][1]
        else:
            err = "errors occurred; run in verbose mode for details"
        raise TestFailed(err)

def run_unittest(*classes):
    """Stolen from Python/Lib/test/test_support."""
    valid_types = (unittest.TestSuite, unittest.TestCase)
    suite = unittest.TestSuite()
    for cls in classes:
        if isinstance(cls, str):
            if cls in sys.modules:
                suite.addTest(unittest.findTestCases(sys.modules[cls]))
            else:
                raise ValueError("str arguments must be keys in sys.modules")
        elif isinstance(cls, valid_types):
            suite.addTest(cls)
        else:
            suite.addTest(unittest.makeSuite(cls))
    run_suite(suite)
