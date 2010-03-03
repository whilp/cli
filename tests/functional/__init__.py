import os

from shutil import rmtree
from tempfile import mkdtemp

from scripttest import TestFileEnvironment

from cli.util import trim

from tests import BaseTest

class FunctionalTest(BaseTest):
    testdir = None
    scriptdir = os.path.join(os.path.dirname(__file__), "scripts")

    def setUp(self):
        self._testdir = self.testdir
        if self._testdir is None:
            self._testdir = mkdtemp(prefix="functests-")
        if not os.path.isdir(self._testdir):
            os.mkdir(self._testdir)
        self.env = TestFileEnvironment(os.path.join(self._testdir, "scripttest"))

        addTypeEqualityFunc = getattr(self, "addTypeEqualityFunc", None)
        if callable(addTypeEqualityFunc):
            addTypeEqualityFunc(str, "assertMultiLineEqual")

    def tearDown(self):
        rmtree(self._testdir)

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
