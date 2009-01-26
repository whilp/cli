import optparse
import unittest
import sys

from cli import Value

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

class ValueTest(BaseTest):
    values = ['']
    options = [
            optparse.Option("-f", "--foo", dest="foo",
                action="store", default="notfoo")
    ]

    def test_short(self):
        self.assertEqual(Value("foo").short, "-f")
        self.assertEqual(Value("Foo").short, "-F")

        # Test override, too.
        value = Value("foo", short="F")
        self.assertEqual(value.short, "-F")

    def test_long(self):
        self.assertEqual(Value("foo").long, "--foo")
        self.assertEqual(Value("foo-bar").long, "--foo-bar")
        self.assertEqual(Value("foo_bar").long, "--foo-bar")

        # Test overrride.
        value = Value("foo", long="long-foo")
        self.assertEqual(value.long, "--long-foo")

    def test_dest(self):
        self.assertEqual(Value("foo").dest, "foo")
        self.assertEqual(Value("foo-bar").dest, "foo_bar")
        self.assertEqual(Value("foo_bar").dest, "foo_bar")

def run_tests(app, *args, **kwargs):
    """[options]

    Run unit tests.
    """
    run_unittest(__name__)

if __name__ == "__main__":
    from cli import App
    app = App(run_tests)
    app.run()
