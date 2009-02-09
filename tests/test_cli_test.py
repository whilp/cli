from cli.test import *

def badfunc(*args, **kwargs):
    raise Exception

class TestRaises:

    def test_simple(self):
        assert raises(Exception, badfunc)

    def test_wrong(self):
        assert not raises(OSError, badfunc)

    def test_sequence(self):
        assert raises((Exception, OSError), badfunc)

    def test_args(self):
        assert raises(Exception, badfunc, "baa")

    def test_exec(self):
        assert raises(Exception, "badfunc('foo')")

    def test_exec_with_args(self):
        assert raises(Exception, "badfunc('foo')", "badarg")
