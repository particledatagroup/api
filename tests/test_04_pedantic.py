"""
Test cases for PdgParticle.
"""
from __future__ import print_function

import unittest

import pdg
from pdg.errors import PdgAmbiguousValueError


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect(pedantic=True)

    def test_properties(self):
        self.assertRaises(PdgAmbiguousValueError, getattr, self.api.get('Q007')[0], 'mass')

    def test_summary(self):
        self.assertRaises(PdgAmbiguousValueError, self.api.get('S013D').best_summary)
