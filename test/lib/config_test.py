import unittest
from screener.lib.config import OptionStr, OptionNum, OptionBool


class TestOptionStr(unittest.TestCase):
    def setUp(self):
        self.c = OptionStr('tests', 'foo', default_val="baa", description="bar", strip=True)

    def test_default(self):
        self.assertEqual(self.c(), "baa")
        self.assertEqual(self.c.get_description(), "bar")

    def test_strip(self):
        self.c.set("fish     ")
        self.assertEqual(self.c(), "fish")

        self.c.set("     cat")
        self.assertEqual(self.c(), "cat")

    def test_float(self):
        self.c.set("1.1")
        self.assertEqual(self.c.get_float(), 1.1)

        self.c.set("1")
        self.assertEqual(self.c.get_float(), 1.0)

    def test_int(self):
        self.c.set("1.1")
        self.assertEqual(self.c.get_int(), 1)

        self.c.set("1")
        self.assertEqual(self.c.get_int(), 1)

class TestOptionNum(unittest.TestCase):
    def test_default(self):
        self.c = OptionNum('tests', 'foo', default_val=1, description="bar")
        self.assertEqual(self.c(), 1)
        self.assertEqual(self.c.get_description(), "bar")

    def test_min(self):
        self.c = OptionNum('tests', 'foo', minval=10)
        self.c.set(1)
        self.assertEqual(self.c(), 10)

    def test_max(self):
        self.c = OptionNum('tests', 'foo', maxval=10)
        self.c.set(100)
        self.assertEqual(self.c(), 10)

    def test_float(self):
        self.c = OptionNum('tests', 'foo', default_val=0.0)
        self.c.set(1.1)
        self.assertEqual(self.c(), 1.1)

        self.c.set("1.1")
        self.assertEqual(self.c(), 1.1)

        self.c.set(100.00)
        self.assertEqual(self.c(), 100.0)

    def test_int(self):
        self.c = OptionNum('tests', 'foo')
        self.c.set(1)
        self.assertEqual(self.c(), 1)

        self.c.set(True)
        self.assertEqual(self.c(), 1)

        self.c.set("1")
        self.assertEqual(self.c(), 1)

class TestOptionBool(unittest.TestCase):
    def setUp(self):
        self.c = OptionBool('tests', 'foo', default_val=True, description="bar")

    def test_default(self):
        self.assertEqual(self.c(), True)
        self.assertEqual(self.c.get_description(), "bar")

    def test_true(self):
        self.c.set(True)
        self.assertEqual(self.c(), True)

        self.c.set(1)
        self.assertEqual(self.c(), True)

        self.c.set("yes")
        self.assertEqual(self.c(), True)

    def test_false(self):
        self.c.set(False)
        self.assertEqual(self.c(), False)

        self.c.set(0)
        self.assertEqual(self.c(), False)

        self.c.set("no")
        self.assertEqual(self.c(), False)

        self.c.set("random")
        self.assertEqual(self.c(), False)

if __name__ == '__main__':
    unittest.main()