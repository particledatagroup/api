"""
Test cases for PdgParticle.
"""
from __future__ import print_function

import unittest

import pdg


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect(pedantic=False)

    def test_name(self):
        self.assertEqual(self.api.get_particle_by_name('p').mcid, 2212)
        self.assertEqual(self.api.get_particle_by_name('pbar').mcid, -2212)

    def test_mcid(self):
        self.assertEqual(self.api.get_particle_by_mcid(5).name, 'b')
        self.assertEqual(self.api.get_particle_by_mcid(-5).name, 'bbar')
        self.assertEqual(self.api.get_particle_by_mcid(5).mcid, 5)
        self.assertEqual(self.api.get_particle_by_mcid(-5).mcid, -5)
        self.assertEqual(self.api.get_particle_by_mcid(11).name, 'e-')
        self.assertEqual(self.api.get_particle_by_mcid(-11).name, 'e+')
        self.assertEqual(self.api.get_particle_by_mcid(100211).name, 'pi(1300)+')
        self.assertEqual(self.api.get_particle_by_mcid(-30323).name, 'K^*(1680)-')
        self.assertEqual(self.api.get_particle_by_mcid(-30323).mcid, -30323)

    def test_quantum_P(self):
        self.assertEqual(self.api.get_particle_by_name('u').quantum_P, '+')
        self.assertEqual(self.api.get_particle_by_name('ubar').quantum_P, '-')
        self.assertEqual(self.api.get_particle_by_name('t').quantum_P, '+')
        self.assertEqual(self.api.get_particle_by_name('tbar').quantum_P, '-')
        self.assertEqual(self.api.get_particle_by_name('p').quantum_P, '+')
        self.assertEqual(self.api.get_particle_by_name('pbar').quantum_P, '-')
        self.assertEqual(self.api.get_particle_by_name('n').quantum_P, '+')
        self.assertEqual(self.api.get_particle_by_name('nbar').quantum_P, '-')
        self.assertEqual(self.api.get_particle_by_mcid(3122).quantum_P, '+')
        self.assertEqual(self.api.get_particle_by_mcid(-3122).quantum_P, '-')


    def test_mass_2022(self):
        if '2022' not in self.api.editions:
            return
        masses = list(self.api.get('q007/2022').masses())
        self.assertEqual(masses[0].pdgid, 'Q007TP/2022')
        self.assertEqual(masses[0].best_summary().value, 172.687433377613)
        self.assertEqual(masses[1].pdgid, 'Q007TP2/2022')
        self.assertEqual(masses[1].best_summary().value, 162.500284698049)
        self.assertEqual(masses[2].pdgid, 'Q007TP4/2022')
        self.assertEqual(masses[2].best_summary().value, 172.463424407473)
        self.assertEqual(self.api.get('s008/2022').mass, 0.139570390983681)
        self.assertEqual(self.api.get('s008/2022').mass_error, 1.8200716040826e-07)

    def test_flags(self):
        self.assertEqual(self.api.get('S008').is_boson, False)
        self.assertEqual(self.api.get('S008').is_quark, False)
        self.assertEqual(self.api.get('S008').is_lepton, False)
        self.assertEqual(self.api.get('S008').is_meson, True)
        self.assertEqual(self.api.get('S008').is_baryon, False)
        self.assertEqual(self.api.get('q007').is_quark, True)
        self.assertEqual(self.api.get('s000').is_boson, True)
        self.assertEqual(self.api.get('S003').is_lepton, True)
        self.assertEqual(self.api.get('S041').is_meson, True)
        self.assertEqual(self.api.get('S016').is_baryon, True)

    def test_properties(self):
        self.assertEqual(len(list(self.api.get('S017').properties('M'))), 2)

    def test_ambiguous_defaults(self):
        self.assertEqual(round(self.api.get('Q007').mass, 1), 172.7)
        self.assertEqual(self.api.get('S013D').best_summary().comment, 'Assuming CPT')
