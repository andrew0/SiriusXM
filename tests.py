import unittest


class TestMethods(unittest.TestCase):
    # If a is equal to b - test is successful
    def test_helloworld(self):
        a = 'hello world'
        b = 'hello world'
        self.assertEqual(a, b)

        
    # If a is not equal to b - test is successful
    def test_helloworldnot(self):
        a = 'hello'
        b = 'world'
        self.assertNotEqual(a, b)


if __name__ == '__main__':
    unittest.main()
