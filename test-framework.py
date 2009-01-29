import unittest

from inspect import isclass, isfunction

suite = unittest.TestSuite()
loader = unittest.TestLoader()

class AppTestCase(object, unittest.TestCase):
    pass

class AppTestLoader(object, unittest.TestLoader):
    ignore_dirs = '.'
    module_extension = ".py"
    module_prefix = "test_"
    module_suffix = "_test"
    func_prefix = "test_"
    class_prefix = "Test"
    testcase_factory = AppTestCase

    def loadTestsFromDirectory(self, directory):
        suite = self.suiteClass()

        root = directory
        for dirpath, dirnames, filenames in os.walk(root):
            # Trim directories list.
            dirnames = [x for x in dirnames \
                    if not x.startswith(self.ignore_dirs)]

            # Search for candidate files.
            candidates = [x for x in filenames if \
                    x.startswith(self.module_prefix) or \
                    x.endswith(self.module_suffix + self.module_extension)]

            for candidate in candidates:
                fullpath = os.path.join(dirpath, candidate)
                suite.addTests(self.loadTestsFromFile(fullpath))

        return suite

    def loadTestsFromFile(self, filename):
        name, _ = os.path.splitext(os.path.basename(filename))
        dirname = os.path.dirname(filename)
        sys.path.insert(0, dirname)
        module = __import__(name)
        return self.loadTestsFromModule(module)

    def loadTestsFromModule(self, module):
        tests = []
        for name, obj in vars(module):
            test = None

            if isclass(obj) and name.startswith(self.class_prefix):
                if issubclass(obj, unittest.TestCase):
                    test = self.loadTestsFromTestCase(obj)
                else:
                    test = self.loadTestsFromTestClass(obj)
            elif isfunction(obj) and name.startswith(self.func_prefix):
                test = self.loadTestsFromTestFunc(obj)

            if test is not None:
                tests.append(test)

        return tests

    def loadTestsFromTestClass(self, obj):
        pass

    def loadTestsFromTestFunc(self, obj):
        class TestFunctionWrapper(self.testcase_factory):
            pass

        name = obj.func_name
        method = self.wrapFunc(obj)
        method.func_name = name
        method.__doc__ = obj.__doc__
        setattr(TestFunctionWrapper, name, method)

        return self.loadTestsFromTestCase(TestFunctionWrapper)

    def wrapFunc(self, func):
        name = func.func_name
        doc = func.__doc__

        def wrappedfunc():
            try:
                result = func()
            except AssertionError:
                # XXX: Do something special here.
                pass
            except:
                # XXX: Do something else here?
                raise

            # XXX: check for generator; do something like py.test
            # here?
            if hasattr(result, "next"):
                pass

        wrappedfunc.func_name = name
        wrappedfunc.__doc__ = doc

        return staticmethod(wrappedfunc)


class AppTestResult(object, unittest.TestResult):

    def __init__(self, app):
        self.app = app
        unittest.TestResult.__init__(self)

    def startTest(self, test):
        TestResult.addSuccess(self, test)
        if not hasattr(test, "...description..."):
            test.description = "DESCR"
        elif not hasattr(test, "name"):
            test.name = str(test)

        self.app.debug("Starting %s (%s)", test.name, test.description)

    def stopTest(self, test):
        TestResult.stopTest(self, test)
        self.app.debug("Finished %s", test.name)

    def addSuccess(self, test):
        TestResult.addSuccess(self, test)
        self.app.log.info("%s ok", test.name)

    def addFailure(self, test, err):
        TestResult.addFailure(self, test, err)
        self.app.log.info("%s failed", test.name)

    def addError(self, test, err):
        TestResult.addFailure(self, test, err)
        self.app.log.info("%s errored", test.name)

class AppTestRunner(object):
    result_factory = AppTestResult

    def __init__(self, app):
        self.app = app
        from timeit import default_timer
        self.timer = default_timer

    def run(self, test):
        result = self.result_factory(self.app)

        # Time and run the test.
        start = self.timer()
        test(result)
        stop = self.timer()

        tests = result.testsRun
        time = datetime.timedelta(seconds=stop - start)
        self.app.log.info("Ran %d test%s in %s", tests,
                plural(tests), time)

        if not result.wasSuccessful():
            failed, errored = [len(x) for x in (results.failures, results.errors)]
            self.app.log.error("%d failure%s, %d error%s", failed,
                    plural(failed), errored, plural(errored))

        return result


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
