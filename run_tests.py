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
    name_inputs = [
            # ({kwarg:value}, {attr:result})
            ({"name": "-foo"}, 
               {"name": "foo",
                "dest": "foo",
                "short": "-f",
                "long": "--foo"}),
            ({"name": "Foo"},
               {"name": "Foo",
                "dest": "Foo",
                "short": "-F",
                "long": "--Foo"}),
            ({"name": "foo-bar"},
               {"name": "foo-bar",
                "dest": "foo_bar",
                "long": "--foo-bar"}),
            ({"name": "foo_bar"},
               {"name": "foo_bar",
                "dest": "foo_bar",
                "long": "--foo-bar"}),
    ]

    short_inputs = [
            ({"name": "foo", "short": "F"}, 
               {"name": "foo",
                "long": "--foo",
                "short": "-F"}),
            ({"name": "foo", "short": "-F"}, 
               {"name": "foo",
                "long": "--foo",
                "short": "-F"}),
    ]

    long_inputs = [
            ({"name": "foo", "long": "foobar"}, 
               {"name": "foo",
                "long": "--foobar",
                "short": "-f"}),
            ({"name": "foo", "long": "Foobar"}, 
               {"name": "foo",
                "long": "--Foobar",
                "short": "-f"}),
    ]

    dest_inputs = [
            ({"name": "foo", "dest": "foobar"}, 
               {"name": "foo",
                "dest": "foobar"}),
            ({"name": "foo", "dest": "foo_bar"}, 
               {"name": "foo",
                "dest": "foo_bar"}),
            ({"name": "foo", "dest": "foo-bar"}, 
               {"name": "foo",
                "dest": "foo_bar"}),
    ]

    def assertEqualOptions(self, first, second):
        """Fail if the attributes for two optparse.Option objects aren't identical.

        optparse.Option doesn't define __hash__, so we get to
        iterate through the .ATTRS attribute for each, checking
        first against second.
        """
        attrs = set(first.ATTRS + second.ATTRS)
        for attr in attrs:
            if not getattr(first, attr) == getattr(second, attr):
                raise self.failureException("%s != %s" % (first, second))

    def _test_inputs(self, inputs):
        for kwargs, attrs in inputs:
            value = Value(**kwargs)
            for attr, result in attrs.items():
                attr = getattr(value, attr)
                self.assertEqual(attr, result)

    def test_name(self):
        self._test_inputs(self.name_inputs)

        self.assertRaises(TypeError, Value, "foo bar")

    def test_short(self):
        self._test_inputs(self.short_inputs)

    def test_long(self):
        self._test_inputs(self.long_inputs)

    def test_dest(self):
        self._test_inputs(self.dest_inputs)

    option_inputs = [
            ({"name": "foo"}, 
               {"name": "foo",
                "dest": "foobar"}),
    ]

    def test_option(self):
        option = optparse.Option("-v", "--verbose",
                dest="verbose",
                action="count",
                default=0,
                help="raise the verbosity")
        value = Value("verbose", 
                action="count",
                default=0,
                help="raise the verbosity")
        self.assertEqualOptions(option, value.option)

def run_tests(app, *args, **kwargs):
    """[options]

    Run unit tests.
    """
    run_unittest(__name__)

if __name__ == "__main__":
    from cli import App
    app = App(run_tests)
    app.run()
