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

from cli.config import ConfigApp, IniConfigParser
from cli.util import StringIO

from tests import AppTest, BaseTest, DecoratorTests

class ConfigParserTest(BaseTest):
    configdict = {
        "parameters": {"verbose": '3', "logfile": "/tmp/foo", "foo": '"bar"'},
        "othersection": {"otherparam": "othervalue"},
    }
    
    def setUp(self):
        self.parser = self.parser_cls()
        self.configfile = StringIO(self.configstr)

class TestIniConfigParser(ConfigParserTest):
    parser_cls = IniConfigParser
    configstr = """\
[parameters]
verbose = 3
logfile = /tmp/foo
foo = "bar"

[othersection]
otherparam = othervalue
"""

    def test_read_valid(self):
        out = self.parser.read(self.configfile)
        self.assertEqual(self.configdict, out)

class TestConfigApp(AppTest, DecoratorTests):
    app_cls = ConfigApp
