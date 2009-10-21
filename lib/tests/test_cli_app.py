"""CLI tools for Python.

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
import operator
import optparse
import unittest
import sys

from cli.app import App
from cli.app import Parameter, ParameterError
from cli.app import CLIParameterHandler, EnvironParameterHandler
from cli.app import Boolean

class BaseTest(unittest.TestCase):

    def setUp(self):
        pass

    def tearDown(self):
        pass

class TestBoolean(BaseTest):

    def test_true(self):
        self.assertEqual(Boolean("yes"), True)
        self.assertEqual(Boolean("Yes"), True)
        self.assertEqual(Boolean("y"), True)
        self.assertEqual(Boolean("Y"), True)
        self.assertEqual(Boolean(10), True)

    def test_false(self):
        self.assertEqual(Boolean(0), False)
        self.assertEqual(Boolean("n"), False)
        self.assertEqual(Boolean("f"), False)
        self.assertEqual(Boolean("somethingelse"), False)
        self.assertEqual(Boolean(0), False)

class TestParameter(BaseTest):

    def setUp(self):
        self.params = Parameter("root")

    def test_attributes(self):
        self.assertEqual(self.params.name, "root")

    def test_add(self):
        bar = Parameter("bar")
        self.params.add(bar)

        self.assertEqual(self.params.bar, bar)
        self.assertEqual(len(self.params.children), 1)

        self.params.add("baz")
        self.assertTrue("baz" in [x.name for x in self.params.children])

        # Test re-writing existing children.
        self.params.add(bar)
        self.assertEquals(bar, self.params.bar)

    def test_remove(self):
        eggs = Parameter("eggs")
        self.params.add(eggs)
        self.params.add("bacon")

        self.assertEqual(len(self.params.children), 2)

        self.params.remove(eggs)
        self.assertEqual(len(self.params.children), 1)
        self.assertRaises(AttributeError,
                operator.attrgetter("eggs"), self.params)
        self.assertFalse("eggs" in [x.name for x in self.params.children])

        self.params.remove("bacon")
        self.assertEqual(len(self.params.children), 0)
        self.assertRaises(AttributeError,
                operator.attrgetter("bacon"), self.params)
        self.assertFalse("eggs" in [x.name for x in self.params.children])

    def test_tree(self):
        self.params.add("bar")
        self.assertEqual(len(self.params.children), 1)

        spam = Parameter("spam")
        self.params.bar.add(spam)
        self.assertEqual(self.params.bar.spam, spam)

    def test_attributes(self):
        self.assertFalse(isinstance(getattr(self.params, "keys"), Parameter))

        keys_parameter = Parameter("keys")
        self.params.add(keys_parameter)
        self.assertFalse(isinstance(getattr(self.params, "keys"), Parameter))
        self.assertTrue(self.params["keys"] is keys_parameter)

    def test_value(self):
        self.params.add("test")
        self.params.test.value = "foo"

        self.assertEqual(self.params.test.value, "foo")

        self.params.test.value = 0
        self.assertEqual(self.params.test.value, 0)

        self.params.add("bar", default=0, coerce=int)
        self.assertEqual(self.params.bar.value, 0)
        
        self.params.bar.value = 10
        self.assertEqual(self.params.bar.value, 10)

        self.params.bar.value = "ten"
        self.assertRaises(ValueError, getattr, self.params.bar, "value")

        self.params.add("foo", default=False)
        self.params.foo.value = "yes"
        self.assertEqual(self.params.foo.value, True)

        class NaughtyObject(object):
            
            def __init__(self, thing=None):
                if isinstance(thing, NaughtyObject):
                    raise TypeError

        naughty = NaughtyObject()
        self.params.add("spam", default=naughty)
        self.assertEqual(self.params.spam.value, naughty)
        self.params.spam.value = "foo"
        self.assertEqual(self.params.spam.value, "foo")

        self.params.add("eggs", default=naughty, coerce=NaughtyObject)
        self.params.eggs.value = NaughtyObject()
        self.assertRaises(TypeError, getattr, self.params.eggs, "value")

    def test_paths(self):
        self.params.add("foo")
        self.params.foo.add("bar")
        self.params.foo.bar.add("baz")

        self.assertEqual(str(self.params.foo.path), "foo")
        self.assertEqual(str(self.params.foo.bar.path), "foo.bar")
        self.assertTrue(len(self.params.foo.bar.path) == 2)

class TestEnvironParameterHandler(BaseTest):
    environ = {
            "FOO": "shouldntbefoo",
            "non_default_name": "foo",
            "BAR": "bar",
    }

    def setUp(self):
        self.app = App(lambda x: x)
        self.params = Parameter("root")
        self.handler = EnvironParameterHandler(self.environ)

    def test_param_name(self):
        self.params.add("foo", "notfoo", var_name="non_default_name")
        self.params.add("bar", "notbar")

        self.handler.handle_parameter(self.params.foo)
        self.handler.handle_parameter(self.params.bar)

        self.assertEqual(self.params.foo.value, "foo")
        self.assertEqual(self.params.bar.value, "bar")

class TestCLIParameterHandler(BaseTest):

    def setUp(self):
        self.app = App(lambda x: x)
        self.handler = CLIParameterHandler([])

class TestApp:

    def test_param_inheritance(self):
        class FooParameter(Parameter):
            pass

        class TestApp(App):
            param_factory = FooParameter

        app = TestApp(lambda x:x)
        app.add_param("foo")
        assert isinstance(app.params.foo, FooParameter)
