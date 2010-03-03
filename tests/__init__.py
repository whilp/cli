try:
    import unittest2 as unittest
except ImportError:
    import unittest

class BaseTest(unittest.TestCase):
    pass
