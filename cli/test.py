"""cli.test - simple test framework

Copyright (c) 2009 Will Maier <will@m.aier.us>

Permission to use, copy, modify, and distribute this software for any
purpose with or without fee is hereby granted, provided that the above
copyright notice and this permission notice appear in all copies.

THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR DISCLAIMS ALL WARRANTIES
WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL THE AUTHOR BE LIABLE FOR
ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.
"""

import datetime
import inspect
import os
import sys
import unittest

from distutils.core import Command
from fnmatch import fnmatch
from timeit import default_timer

from util import plural

def timer(callable, *args, **kwargs):
    """Time and run callable with args and kwargs.

    Returns a tuple (timedelta, returned), where 'timedelta' is a
    datetime.timedelta object representing the time it took to run
    the callable and 'returned' is the output from callable.
    """
    start = default_timer()
    returned = callable(*args, **kwargs)
    stop = default_timer()
    duration = datetime.timedelta(seconds=stop - start)

    return returned, duration

def raises(exception, callable, *args, **kwargs):
    """Return True if callable raises exception when passed args and kwargs.

    If callable is a string and args and kwargs are empty, the
    string will be passed to the exec statement. If any other
    exception is raised, return False.
    """
    try:
        if isinstance(callable, str) and not (args or kwargs):
            exec(callable)
        else:
            callable(*args, **kwargs)
    except exception:
        return True
    except:
        return False

class AppTestCase(unittest.TestCase, object):
    overridden_methods = ["run"]
    root = ''

    @property
    def testmethod(self):
        name = getattr(self, "_testMethodName", None)
        method = getattr(self, name, None)
        return method

    @property
    def lineno(self):
        lineno = getattr(self.testmethod, "lineno",
                inspect.getsourcelines(self.testmethod)[1])
        return lineno

    @property
    def filename(self):
        filename = getattr(self.testmethod, "filename",
                inspect.getsourcefile(self.testmethod))
        return filename

    @property
    def module(self):
        module = getattr(self.testmethod, "module",
                inspect.getmodule(self.testmethod))
        return module

    @property
    def cls(self):
        return getattr(self.testmethod, "im_class", None)

    @property
    def methodname(self):
        func = getattr(self.testmethod, "im_func", None)
        if func is None:
            func = self.testmethod

        return func.func_name

    @property
    def name(self):
        delim = '.'
        name = [inspect.getmodulename(self.filename), self.methodname]
        if self.cls:
            name.insert(1, self.cls.__name__)

        return delim.join(name) + "()"

    def setUp(self):
        setup_method = getattr(self, "setup_method", None)
        if callable(setup_method):
            setup_method(self.testmethod)
        unittest.TestCase.setUp(self)

    def tearDown(self):
        teardown_method = getattr(self, "teardown_method", None)
        if callable(teardown_method):
            teardown_method(self.testmethod)
        else:
            unittest.TestCase.tearDown(self)

    def run(self, result=None):
        """Run the test.
        
        Before running the test, check the test method for a
        '.disabled' attribute. If that attribute is not false, skip
        the test and call the result's .addSkip() method.
        """
        disabled = getattr(self.testmethod, "disabled", 
            getattr(self, "disabled", None))
        if disabled:
            result.addSkip(self, disabled)
        else:
            unittest.TestCase.run(self, result)

class AppTestSuite(unittest.TestSuite, object):

    def addTest(self, test):
        matches = True
        filename = getattr(test, "filename", None)

        if filename is not None and self.keyword:
            try:
                classname = test.cls.__name__
            except:
                classname = ""
            modulename = test.module.__name__

            tests = [
                    os.path.basename(test.filename),
                    classname,
                    modulename,
                    test.methodname
            ]
            matches = [x for x in tests if fnmatch(x, self.keyword)]

        if matches:
            unittest.TestSuite.addTest(self, test)

class AppTestLoader(unittest.TestLoader, object):
    """Extend the base unittest.TestLoader.

    AppTestLoaders know about app and its facilties and can
    therefore log or adjust their behavior based on parameters.
    Additionally, the AppTestLoader incorporates the following
    behaviors:
        
        * Within tests are sorted by their position in their source
          files. Two tests from the same sourcefile will be compared
          by the line number on which each object is defined;
          otherwise, the filenames of the source files are compared.
        * Additional .loadTestsFromDirectory() method to discover
          and load tests found by walking a path.
        * Additional .loadTestsFromModule() method which discovers
          tests defined in a module. These tests are not limited to
          classic unittest.TestCase subclasses. Instead, plain
          functions and plain classes that follow a generic naming
          convention are considered in addition to
          unittest.TestCases.

    None of the above extensions break standard unittest
    functionality. Many of them are intended to replicate the ease
    of use of py.test without the addition of black magic.
    """
    ignore_dirs = '.'
    module_extension = ".py"
    module_prefix = "test_"
    module_suffix = "_test"
    func_prefix = "test_"
    class_prefix = "Test"
    testcase_factory = AppTestCase
    testsuite_factory = AppTestSuite

    # Unittest synonyms.
    suiteClass = testsuite_factory
    testMethodPrefix = func_prefix
    sortTestMethodsUsing = None

    def __init__(self, app, root="", keyword=""):
        self.app = app
        self.testcase_factory.root = root
        self.suiteClass.keyword = keyword

    @staticmethod
    def sort_methods(cls, x, y):
        """Sort objects based on their appearance in a source file.
        
        If they both were defined in the same file, the object which
        was defined earlier is considered "less than" the object
        which was defined later. If they were defined in different
        source files, the source filenames will be compared
        alphabetically.
        """
        args = [getattr(cls, name) for name in x, y]
        x_file, y_file = [inspect.getsourcefile(obj) for obj in args]
        if x_file == y_file:
            x, y = [inspect.getsourcelines(obj)[1] for obj in args]
        else:
            x, y = x_file, y_file
        return cmp(x, y)

    def getTestCaseNames(self, testCaseClass):
        """Sort the test case names using .sort_methods()."""
        names = unittest.TestLoader.getTestCaseNames(self, testCaseClass)
        def sorter(x, y):
            return self.sort_methods(testCaseClass, x, y)
        names.sort(sorter)

        return names

    def loadTestsFromDirectory(self, directory):
        """Load tests from a directory.

        The directory may be a relative or absolute path. All
        modules found under that directory with the
        .module_extension and matching either the .module_prefix or
        .module_suffix attributes will be considered. Within those
        modules, functions matching the .func_prefix attribute,
        classes matching the .class_prefix attribute or
        unittest.TestCase subclasses will be loaded.
        """
        directory = os.path.abspath(directory)
        suite = self.suiteClass()

        root = directory
        self.app.log.debug("Examining %s", root)
        for dirpath, dirnames, filenames in os.walk(root):
            # Trim directories list.
            dirnames = [x for x in dirnames \
                    if not x.startswith(self.ignore_dirs)]

            # Search for candidate files.
            candidates = [full for base, ext, full in \
                    [os.path.splitext(x) + (x,) for x in filenames] \
                    if ext == self.module_extension and \
                    (base.startswith(self.module_prefix) or \
                    base.endswith(self.module_suffix))]

            for candidate in candidates:
                fullpath = os.path.join(dirpath, candidate)
                self.app.log.debug("Adding %s", fullpath)
                suite.addTests(self.loadTestsFromFile(fullpath))

        return suite

    def loadTestsFromFile(self, filename):
        """Load a module, discovering valid test cases within it."""
        name, _ = os.path.splitext(os.path.basename(filename))
        dirname = os.path.dirname(filename)
        sys.path.insert(0, dirname)
        module = __import__(name)
        return self.loadTestsFromModule(module)

    def loadTestsFromModule(self, module):
        """Discover valid test cases within a module."""
        tests = []

        objects = vars(module).items()
        functions = [(name, obj) for name, obj in objects if \
                name.startswith(self.func_prefix) and inspect.isfunction(obj)]
        unittests = [(name, obj) for name, obj in objects if \
                inspect.isclass(obj) and issubclass(obj, unittest.TestCase)]
        classes = [(name, obj) for name, obj in objects if \
                (inspect.isclass(obj) and not issubclass(obj, unittest.TestCase))
                and name.startswith(self.class_prefix)]

        functions = [self.loadTestCaseFromFunction(f) for _, f in functions]
        unittests = [self.loadTestCaseFromUnittest(u) for _, u in unittests]
        classes = [self.loadTestCaseFromTestClass(c) for _, c in classes]

        tests = unittests + classes + functions
        tests = [self.loadTestsFromTestCase(x) for x in tests]

        return tests

    def loadTestCaseFromFunction(self, function):
        """Generate a TestCase for a plain function."""
        class FunctionTestCase(self.testcase_factory):
            """To collect module-level tests."""
        module = inspect.getmodule(function)

        # This is a plain old function, so we make it into a
        # method and attach it to the dummy TestCase.
        self.attach_function(FunctionTestCase, function)

        # Check the module for py.test hooks.
        setup_class = getattr(module, "setup_class", None)
        teardown_class = getattr(module, "teardown_class", None)

        # Translate py.test hooks into unittest hooks.
        if callable(setup_class):
            self.attach_function(FunctionTestCase, setup_class, "setUp")
        if callable(teardown_class):
            self.attach_function(FunctionTestCase, teardown_class, "tearDown")

        return FunctionTestCase

    def loadTestCaseFromUnittest(self, unittest):
        """Generate a useful TestCase from a plain unittest.TestCase."""
        # This is a standard unittest.TestCase.  Transport the
        # necessary properties from our testcase (so that the
        # Results and Runner classes can work with it) and
        # replace the dummy TestCase with it.
        methods = self.testcase_factory.overridden_methods
        for name, member in vars(self.testcase_factory).items():
            if isinstance(member, property) or name in methods:
                setattr(unittest, name, member)
        unittest.root = self.testcase_factory.root

        return unittest
    
    def loadTestCaseFromTestClass(self, cls):
        """Generate a TestCase from a non-Unittest test class."""
        class PlainTestCase(self.testcase_factory):
            """To collect plain class-based tests."""

        # This is a plain test class that doesn't subclass
        # unittest.TestCase. Transport its attributes over to our
        # dummy TestCase.
        for name in dir(cls):
            attr = getattr(cls, name)
            if not hasattr(PlainTestCase, name):
                # XXX: Cross our fingers here and hope we don't skip
                # anything crucial.
                if callable(attr):
                    self.attach_function(PlainTestCase, attr, name, cls)
                else:
                    setattr(PlainTestCase, name, attr)

        # Get the setup and teardown methods from the class'
        # __dict__. This technique circumvents the type check on the
        # methods so that they don't complain about getting TestCase
        # instances.
        setup_method = getattr(cls, "setup_method", None)
        teardown_method = getattr(cls, "teardown_method", None)
        if callable(setup_method):
            self.attach_function(PlainTestCase, setup_method, old=cls)
        if callable(teardown_method):
            self.attach_function(PlainTestCase, teardown_method, old=cls)
        PlainTestCase.__name__ = cls.__name__

        return PlainTestCase

    @staticmethod
    def attach_function(new, function, name="", old=None):
        """Wrap a plain function to make it a useful TestCase method."""
        if not name:
            name = function.func_name
        doc = function.__doc__

        if old is None:
            setattr(new, name, staticmethod(function))
        else:
            # Search the old class' mro for a __dict__ that contains
            # the function. We need to do this to avoid the 'unbound
            # instance requires...' TypeError.
            oldf = None
            for cls in inspect.getmro(old):
                oldf = cls.__dict__.get(name, None)
                if oldf is not None:
                    break

            f = lambda *a, **k: oldf(*a, **k)
            f.__name__ = name
            f.__doc__ = doc
            f.lineno = inspect.getsourcelines(function)[1]
            f.filename = inspect.getsourcefile(function)
            f.module = inspect.getmodule(function)
            setattr(new, name, f)

class AppTestResult(unittest.TestResult, object):
    """Extend the base unittest.TestResult.

    In addition to the standard unittest behavior, AppTestResults
    can:
        
        * Generate useful-yet-brief status messages.
        * Report the running time for each test.

    Most of these features were inspired by py.test.
    """

    def __init__(self, app):
        self.app = app
        unittest.TestResult.__init__(self)

        self.skipped = []
        self.start = 0
        self.stop = 0

    def status_message(self, test, status):
        time = self.time
        filename = test.filename
        if filename.startswith(test.root):
            filename = test.filename[len(test.root):].lstrip(os.path.sep)
        fields = {
                "seconds": time.seconds + (time.microseconds/10.0**6),
                "status": status,
                "name": test.name,
                "path": "%s:%d" % (filename, test.lineno)
        }

        format = "%(seconds)3.3f %(status)5s %(path)-25s %(name)s"
        return format % fields

    @property
    def time(self):
        return datetime.timedelta(seconds=self.stop - self.start)

    def startTest(self, test):
        unittest.TestResult.startTest(self, test)
        self.start = default_timer()

    def stopTest(self, test):
        unittest.TestResult.stopTest(self, test)

    def addSuccess(self, test):
        self.stop = default_timer()
        unittest.TestResult.addSuccess(self, test)
        self.app.log.info(self.status_message(test, "ok"))

    def addFailure(self, test, err):
        self.stop = default_timer()
        unittest.TestResult.addFailure(self, test, err)
        self.app.log.warning(self.status_message(test, "fail"))

    def addError(self, test, err):
        self.stop = default_timer()
        unittest.TestResult.addFailure(self, test, err)
        self.app.log.error(self.status_message(test, "error"))

    def addSkip(self, test, message):
        self.app.log.info(self.status_message(test, "skip"))
        self.skipped.append((test, message))

class AppTestRunner(object):
    """Extend the base unittest.TextTestRunner.

    AppTestRunner can do the following in addition to the standard
    behavior:

        * Log via app.log channels.
        * Generate AppTestResults and use their extended
          capabilities.
    """
    result_factory = AppTestResult

    def __init__(self, app):
        self.app = app

    def run(self, test):
        result = self.result_factory(self.app)

        # Time and run the test.
        _, time = timer(test, result)

        tests = result.testsRun
        self.app.log.info("Ran %d test%s in %s", tests,
                plural(tests), time)

        # If we failed, dump tracebacks and other helpful
        # information.
        if not result.wasSuccessful() or result.skipped:
            failed, errored, skipped = [len(x) for x in 
                    (result.failures, result.errors, result.skipped)]
            self.app.log.error("%d failure%s, %d error%s, %d skipped", failed,
                    plural(failed), errored, plural(errored), skipped)

            if result.skipped:
                self.app.stderr.write('\n%s\n' % (70 * '='))
                self.app.stderr.write("Skipped:\n".upper())
                for test, message in result.skipped:
                    self.app.stderr.write(70 * '-' + '\n')
                    self.app.stderr.write("%s:\n" % test.name)
                    self.app.stderr.write("    file:\t%s:%d\n" %
                            (test.filename, test.lineno))
                    self.app.stderr.write("    reason:\t%s" % message)
                    self.app.stderr.write("\n")

            if result.errors:
                self.app.stderr.write('\n%s\n' % (70 * '='))
                self.app.stderr.write("Errors:\n".upper())
                for test, traceback in result.errors:
                    self.app.stderr.write(70 * '-' + '\n')
                    self.app.stderr.write("%s:%d\n\n" % (test.filename, test.lineno))
                    self.app.stderr.write(traceback)
                    self.app.stderr.write("\n")

            if result.failures:
                self.app.stderr.write('\n%s\n' % (70 * '='))
                self.app.stderr.write("Failures:\n".upper())
                for test, traceback in result.failures:
                    self.app.stderr.write(70 * '-' + '\n')
                    self.app.stderr.write("%s:%d\n\n" % (test.filename, test.lineno))
                    self.app.stderr.write(traceback)
                    self.app.stderr.write("\n")

        return result

def test(app, *args):
    """[options] [directory]

    Collect and run unit tests. If 'directory' is specified,
    collect all unit tests under that directory. If it is not
    specified, collect all tests under the current directory.
    """
    directory = args and args[0] or '.'

    runner = AppTestRunner(app)
    suite = AppTestSuite()
    loader = AppTestLoader(app, root=directory, keyword=app.params.keyword)

    suite.addTests(loader.loadTestsFromDirectory(directory))
    result = runner.run(suite)

    if not result.wasSuccessful():
        return 1
    else:
        return 0

class TestCommand(Command):
    user_options = [
            ("keyword=", "k", "only run tests matching KEYWORD")]

    def initialize_options(self):
        self.keyword = ""

    def finalize_options(self):
        pass

    def run(self):
        from cli import App
        app = App(test, argv=[os.getcwd()])
        app.params.verbose.default = self.verbose
        app.add_param("keyword", self.keyword, "only run tests matching KEYWORD")
        app.run()
