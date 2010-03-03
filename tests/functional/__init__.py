import os

from tempfile import mkdtemp

from scripttest import TestFileEnvironment

from cli.util import trim

from tests import BaseTest

class FunctionalTest(BaseTest):
    testdir = None
    scriptdir = os.path.join(os.path.dirname(__file__), "scripts")

    def setUp(self):
        testdir = self.testdir
        if self.testdir is None:
            testdir = mkdtemp(prefix="functests-")
        self.env = TestFileEnvironment(os.path.join(testdir, "scripttest"))

        addTypeEqualityFunc = getattr(self, "addTypeEqualityFunc", None)
        if callable(addTypeEqualityFunc):
            addTypeEqualityFunc(str, "assertMultiLineEqual")

    def run_script(self, script, *args, **kwargs):
        script = os.path.join(self.scriptdir, script)
        return self.env.run(script, *args, **kwargs)

    def assertScriptDoes(self, result, stdout='', stderr='', returncode=0, trim_output=True):
        if trim_output:
            stdout, stderr = trim(stdout), trim(stderr)
        self.assertEqual(result.returncode, returncode,
            "expected returncode %d, got %d" % (result.returncode, returncode))
        self.assertEqual(result.stdout, stdout,
            "unexpected output on stdout")
        self.assertEqual(result.stderr, stderr,
            "unexpected output on stderr")
