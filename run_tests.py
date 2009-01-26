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

    def _test_inputs(self, inputs):
        for kwargs, attrs in inputs:
            value = Value(**kwargs)
            for attr, result in attrs.items():
                attr = getattr(value, attr)
                self.assertEqual(attr, result)

    def test_name(self):
        self._test_inputs(self.name_inputs)

    def test_short(self):
        self._test_inputs(self.short_inputs)

    def test_long(self):
        simple = [
                ("foo", "--foo"),
                ("foo-bar", "--foo-bar"),
                ("foo_bar", "--foo-bar")
        ]

        for name, result in simple:
            self.assertEqual(Value(name).long, result)

        # Test overrride.
        override = [
                ("long-foo", "--long-foo")
        ]

        for long, result in override:
            value = Value("foo", long=long)
            self.assertEqual(value.long, result)

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
