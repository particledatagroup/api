"""
Test cases for some use examples.
"""
from __future__ import print_function

import unittest

import pdg


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect(pedantic=False)

    def test_dm(self):
        p = self.api.get_particle_by_name('p')
        n = self.api.get_particle_by_name('n')
        dm = n.mass - p.mass
        self.assertEqual(round(dm, 5), 0.00129)
