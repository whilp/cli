import operator
import optparse
import unittest
import sys

from cli import Parameter, ParameterError

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

class ParameterTests(BaseTest):

    def test_attributes(self):
        parameter = Parameter("foo")
        self.assertEqual(parameter.name, "foo")

    def test_add(self):
        foo = Parameter("foo")
        bar = Parameter("bar")
        foo.add(bar)

        self.assertEqual(foo.bar, bar)
        self.assertEqual(len(foo.children), 1)

        foo.add("baz")
        self.assertTrue("baz" in [x.name for x in foo.children])

        # The .name attribute should always exist.
        self.assertRaises(ParameterError, foo.add, "name")

        # Test re-writing existing children.
        foo.add(bar)
        self.assertEquals(bar, foo.bar)

    def test_remove(self):
        spam = Parameter("spam")
        eggs = Parameter("eggs")
        spam.add(eggs)
        spam.add("bacon")

        self.assertEqual(len(spam.children), 2)

        spam.remove(eggs)
        self.assertEqual(len(spam.children), 1)
        self.assertRaises(AttributeError, operator.attrgetter("eggs"), spam)
        self.assertFalse("eggs" in [x.name for x in spam.children])

        spam.remove("bacon")
        self.assertEqual(len(spam.children), 0)
        self.assertRaises(AttributeError, operator.attrgetter("bacon"), spam)
        self.assertFalse("eggs" in [x.name for x in spam.children])

        # .name is non-Parameter attribute which we can't remove.
        self.assertRaises(ParameterError, spam.remove, "name")

    def test_tree(self):
        root = Parameter("root")
        root.add("bar")
        self.assertEqual(len(root.children), 1)

        spam = Parameter("spam")
        root.bar.add(spam)
        self.assertEqual(root.bar.spam, spam)

        self.assertEqual(root.bar.path, "bar")
        self.assertEqual(root.bar.spam.path, "bar.spam")

def run_tests(app, *args, **kwargs):
    """[options]

    Run unit tests.
    """
    run_unittest(__name__)

if __name__ == "__main__":
    run_unittest(__name__)
    #from cli import App
    #app = App(run_tests)
    #app.run()
