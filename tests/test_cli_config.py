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

from cli.config import *
from cli.util import StringIO

from tests import AppTest, BaseTest, DecoratorTests

class ConfigParserTest(BaseTest):
    configdict = {
        u"parameters": {u"verbose": u'3', u"logfile": u"/tmp/foo", u"foo": u"bar"},
        u"othersection": {u"otherparam": u"othervalue"},
    }
    
    def setUp(self):
        self.parser = self.parser_cls()
        self.configfile = StringIO(self.configstr)

class ParserTests(object):

    def test_read_valid(self):
        out = self.parser.read(self.configfile)
        self.assertEqual(self.configdict, out)

    def test_equivalent(self):
        tmp = StringIO()
        parsed = self.parser.read(self.configfile)
        self.parser.write(parsed, tmp)
        tmp.seek(0)
        parsed2 = self.parser.read(tmp)
        self.assertEqual(parsed, parsed2)

class TestIniConfigParser(ConfigParserTest, ParserTests):
    parser_cls = IniConfigParser
    configstr = """\
[parameters]
verbose = 3
logfile = /tmp/foo
foo = bar

[othersection]
otherparam = othervalue
"""

class TestJSONConfigParser(ConfigParserTest, ParserTests):
    parser_cls = JSONConfigParser
    configstr = """\
{"parameters":
        {"verbose": "3", "logfile": "/tmp/foo", "foo": "bar"},
"othersection":
        {"otherparam": "othervalue"}
}
"""

class TestPythonConfigParser(ConfigParserTest, ParserTests):
    parser_cls = PythonConfigParser
    configstr = """\
parameters = {"verbose": "3", "logfile": "/tmp/foo", "foo": "bar"}
othersection = {"otherparam": "othervalue"}
"""

class TestConfigApp(AppTest, DecoratorTests):
    app_cls = ConfigApp

    def setUp(self):
        self.configfile = StringIO("""\
{
    "parameters": {
        "verbose": 3,
        "logfile": "/tmp/foo"
    },
    "othersection": {
        "otherkey": "othervalue"
    }
}""")
        self.kwargs = {
            "configfile": self.configfile,
            "configparser_factory": JSONConfigParser,
        }
        super(TestConfigApp, self).setUp()

    def test_config_parsing_params(self):
        self.app.configparser_factory = JSONConfigParser
        self.app.configfile = self.configfile
        self.app.run()
        self.assertEqual(self.app.params.verbose, 3)
