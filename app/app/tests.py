"""
Sample tests
"""

from django.test import SimpleTestCase
from app import calc

class CalcTests(SimpleTestCase):
    """Tests functionality of calc module"""

    def test_add_numbers(self):
        """Test for adding two numbers"""
        res = calc.add(4, 3)
        self.assertEqual(res, 7)

    def test_substract_numbers(self):
        res = calc.sub(5, 2)
        self.assertEqual(res, 3)
    
    def test_multiply_numbers(self):
        res = calc.multiply(7, 2)
        self.assertEqual(res, 14)