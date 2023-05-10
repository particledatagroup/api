"""
Test cases for PdgParticle.
"""
from __future__ import print_function

import unittest

import pdg
from pdg.errors import PdgAmbiguousValue


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect()

    def test_mcid(self):
        self.assertEqual(self.api.get_particle_by_mcid(5).name(), 'b')
        self.assertEqual(self.api.get_particle_by_mcid(-5).name(), 'bbar')
        self.assertEqual(self.api.get_particle_by_mcid(11).name(), 'e-')
        self.assertEqual(self.api.get_particle_by_mcid(-11).name(), 'e+')
        self.assertEqual(self.api.get_particle_by_mcid(100211).name(), 'pi(1300)+')
        self.assertEqual(self.api.get_particle_by_mcid(-30323).name(), 'K^*(1680)-')
        self.assertEqual(self.api.get_particle_by_mcid(5).mcid(), 5)
        self.assertEqual(self.api.get_particle_by_mcid(-5).mcid(), -5)
        self.assertEqual(self.api.get_particle_by_mcid(-30323).mcid(), -30323)

    def test_mass_2022(self):
        if '2022' not in self.api.editions():
            return
        self.assertRaises(PdgAmbiguousValue, self.api.get('q007').mass)
        masses = list(self.api.get('q007/2022').masses())
        self.assertEqual(masses[0].pdgid, 'Q007TP/2022')
        self.assertEqual(masses[0].best_value().value(), 172.687433377613)
        self.assertEqual(masses[1].pdgid, 'Q007TP2/2022')
        self.assertEqual(masses[1].best_value().value(), 162.500284698049)
        self.assertEqual(masses[2].pdgid, 'Q007TP4/2022')
        self.assertEqual(masses[2].best_value().value(), 172.463424407473)
        self.assertEqual(self.api.get('s008/2022').mass().value(), 0.139570390983681)

    def test_flags(self):
        self.assertEqual(self.api.get('S008').is_boson(), False)
        self.assertEqual(self.api.get('S008').is_quark(), False)
        self.assertEqual(self.api.get('S008').is_lepton(), False)
        self.assertEqual(self.api.get('S008').is_meson(), True)
        self.assertEqual(self.api.get('S008').is_baryon(), False)
        self.assertEqual(self.api.get('q007').is_quark(), True)
        self.assertEqual(self.api.get('s000').is_boson(), True)
        self.assertEqual(self.api.get('S003').is_lepton(), True)
        self.assertEqual(self.api.get('S041').is_meson(), True)
        self.assertEqual(self.api.get('S016').is_baryon(), True)
