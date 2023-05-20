"""
Test cases for utility functions.
"""
from __future__ import print_function

import unittest

from pdg import utils


class TestUtils(unittest.TestCase):

    def test_rounding(self):
        self.assertEqual(utils.pdg_round(0.827, 0.119), (0.83, 0.12))
        self.assertEqual(utils.pdg_round(0.827, 0.367), (0.8, 0.4))
        self.assertEqual(utils.pdg_round(12.3456, .99), (12.3, 1.0))

    def test_parse_id(self):
        self.assertEqual(utils.parse_id('s043m/2020'), ('S043M', '2020'))
        self.assertEqual(utils.parse_id('s043m'), ('S043M', None))

    def test_base_id(self):
        self.assertEqual(utils.base_id('q007/2020'), 'Q007')

    def test_make_id(self):
        self.assertEqual(utils.make_id('q007', None), 'Q007')
        self.assertEqual(utils.make_id('q007', '2020'), 'Q007/2020')


if __name__ == '__main__':
    unittest.main()
