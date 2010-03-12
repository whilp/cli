"""CLI tools for Python.

Copyright (c) 2009-2010 Will Maier <will@m.aier.us>

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

from cli.app import Application, CommandLineApp
from cli.util import StringIO

from tests.functional import FunctionalTest

class TestApplication(FunctionalTest):

    def test_run(self):
        result = self.run_script("application")
        self.assertScriptDoes(result, stdout="""\
            This is a basic application
            Its name is 'application'
            Its version is 'None'
            Its running with the following arguments: None
            Its description is:
            None
            And it's done""")

    def test_raises_an_exception(self):
        result = self.run_script("brokenapp")
		result.stderr = self.unitrace(result.stderr)
"""
Traceback (most recent call last):
  File "/home/will/share/cli/tests/functional/scripts/brokenapp", line 14, in <module>
    application.run()
  File "/home/will/share/cli/lib/cli/app.py", line 202, in run
    returned = self.main(self)
  File "/home/will/share/cli/tests/functional/scripts/brokenapp", line 10, in application
    whoops = 1/0
ZeroDivisionError: integer division or modulo by zero
"""
        self.assertScriptDoes(result, returncode=1, stdout="""\
            This is a broken application
            What happens if we divide 1 by 0?""")
