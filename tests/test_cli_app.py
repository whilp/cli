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

from cli.app import Application

from tests import AppTest

class TestApplication(AppTest):
    
    def setUp(self):
        @Application
        def app(app):
            """This is the description."""
            pass
        self.app = app

    def test_discover_name(self):
        self.assertEqual(self.app.name, "app")

    def test_decorate_callable(self):
        @Application
        def foo(app):
            pass
        self.assertEqual(foo.name, "foo")

    def test_instantiate_and_decorate_callable(self):
        @Application(name="foo")
        def bar(app):
            pass
        self.assertEqual(bar.name, "foo")

    def test_wrap_non_function_callable(self):
        @Application
        class foo(object):
            def __call__(self, app):
                pass

        self.assertEqual(foo.name, "foo")
