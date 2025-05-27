"""
Test cases for PdgParticle.
"""
from __future__ import print_function

import unittest

import pdg
from pdg.decay import PdgBranchingFraction, PdgDecayProduct
from pdg.errors import PdgAmbiguousValueError, PdgNoDataError
from pdg.particle import PdgParticle


class TestData(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect(pedantic=False)

    def setUp(self):
        self.api.pedantic = False

    def test_all_particle_data(self):
        n_errors = 0
        for plist in self.api.get_particles():
            for p in plist:
                try:
                    p._get_particle_data()
                except Exception as e:
                    n_errors += 1
                    print(e)
        self.assertEqual(n_errors, 0)

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
        # self.assertEqual(self.api.get_particle_by_mcid(39).name, 'graviton')
        self.assertEqual(self.api.get_particle_by_mcid(100211).name, 'pi(1300)+')
        self.assertEqual(self.api.get_particle_by_mcid(-30323).name, 'K^*(1680)-')
        self.assertEqual(self.api.get_particle_by_mcid(-30323).mcid, -30323)

    def test_equivalent_names(self):
        p1 = self.api.get_particle_by_name('K(S)')
        p2 = self.api.get_particle_by_name('K(S)0')
        self.assertEqual(p1.pdgid, p2.pdgid)

    def test_generic_names(self):
        self.assertRaises(PdgAmbiguousValueError,
                          lambda: self.api.get_particle_by_name('e'))
        self.assertRaises(PdgAmbiguousValueError,
                          lambda: self.api.get_particle_by_name('pi'))
        mus = list(self.api.get_particles_by_name('mu'))
        self.assertEqual(len(mus), 2)
        self.assertEqual(mus[0].mcid, 13)
        self.assertEqual(mus[1].mcid, -13)

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
        masses = list(self.api.get('q007/2022')[0].masses())
        self.assertEqual(masses[0].pdgid, 'Q007TP/2022')
        self.assertEqual(round(masses[0].best_summary().value,9), 172.687433378)
        self.assertEqual(masses[1].pdgid, 'Q007TP2/2022')
        self.assertEqual(round(masses[1].best_summary().value,9), 162.500284698)
        self.assertEqual(masses[2].pdgid, 'Q007TP4/2022')
        self.assertEqual(round(masses[2].best_summary().value,9), 172.463424407)
        self.assertEqual(round(self.api.get('s008/2022')[0].mass,9), 0.139570391)
        self.assertEqual(round(self.api.get('s008/2022')[0].mass_error,16), 1.820071604e-07)

    def test_best_masses(self):
        self.assertEqual(round(self.api.get_particle_by_name('p').mass, 3), 0.938)
        self.assertEqual(round(self.api.get_particle_by_name('pi+').mass, 3), 0.140)
        self.assertEqual(round(self.api.get_particle_by_name('e-').mass, 6), 0.000511)
        self.assertEqual(round(self.api.get_particle_by_name('tbar').mass, 1), 172.6)
        self.assertEqual(round(self.api.get_particle_by_name('B+').mass, 2), 5.28)
        self.assertEqual(round(self.api.get_particle_by_name('Z').mass, 1), 91.2)

    def test_flags(self):
        self.assertEqual(self.api.get('S008')[0].is_boson, False)
        self.assertEqual(self.api.get('S008')[0].is_quark, False)
        self.assertEqual(self.api.get('S008')[0].is_lepton, False)
        self.assertEqual(self.api.get('S008')[0].is_meson, True)
        self.assertEqual(self.api.get('S008')[0].is_baryon, False)
        self.assertEqual(self.api.get('q007')[0].is_quark, True)
        self.assertEqual(self.api.get('s000')[0].is_boson, True)
        self.assertEqual(self.api.get('S003')[0].is_lepton, True)
        self.assertEqual(self.api.get('S041')[0].is_meson, True)
        self.assertEqual(self.api.get('S016')[0].is_baryon, True)

    def test_properties(self):
        self.assertEqual(len(list(self.api.get('S017')[0].properties('M'))), 2)

    def test_ambiguous_defaults(self):
        self.assertEqual(round(self.api.get('Q007')[0].mass, 1), 172.6)
        self.assertEqual(self.api.get('S013D').best_summary().comment, 'Assuming CPT')

    def test_best_widths_and_lifetimes(self):
        pi0 = self.api.get_particle_by_name('pi0')
        self.assertTrue(pi0.has_lifetime_entry)
        self.assertFalse(pi0.has_width_entry)
        self.assertEqual(round(pi0.lifetime * 1e17, 2), 8.43)
        self.assertEqual(round(pi0.lifetime_error * 1e17, 3), 0.134)
        self.api.pedantic = True
        self.assertRaises(PdgNoDataError, lambda: pi0.width)
        self.assertRaises(PdgNoDataError, lambda: pi0.width_error)
        self.api.pedantic = False
        self.assertEqual(round(pi0.width * 1e9, 2), 7.81)
        self.assertEqual(round(pi0.width_error * 1e9, 3), 0.125)

        W = self.api.get_particle_by_name('W+')
        self.assertTrue(W.has_width_entry)
        self.assertFalse(W.has_lifetime_entry)
        self.assertEqual(round(W.width, 3), 2.137)
        self.assertEqual(round(W.width_error, 4), 0.0537)
        self.api.pedantic = True
        self.assertRaises(PdgNoDataError, lambda: W.lifetime)
        self.assertRaises(PdgNoDataError, lambda: W.lifetime_error)
        self.api.pedantic = False
        self.assertEqual(round(W.lifetime * 1e25, 2), 3.08)
        self.assertEqual(round(W.lifetime_error * 1e25, 3), 0.077)

    def test_Kstar_892(self):
        ps = self.api.get('M018')
        ps = sorted(ps, key=lambda p: p.name)
        self.assertEqual([p.name for p in ps],
                         ['K^*(892)+', 'K^*(892)-', 'K^*(892)0', 'Kbar^*(892)0'])
        self.assertEqual([len(list(p.masses())) for p in ps],
                         [3, 3, 2, 2])
        self.assertEqual([len(list(p.widths())) for p in ps],
                         [2, 2, 1, 1])
        self.assertEqual([len(list(p.lifetimes())) for p in ps],
                         [0, 0, 0, 0])

        self.api.pedantic = True
        self.assertRaises(PdgAmbiguousValueError, lambda: ps[0].mass)
        self.assertRaises(PdgAmbiguousValueError, lambda: ps[0].width)
        self.assertRaises(PdgNoDataError, lambda: ps[0].lifetime)
        self.assertEqual(ps[0].charge, 1)

        self.api.pedantic = False
        self.assertIsNotNone(ps[0].mass)
        self.assertIsNotNone(ps[0].width)
        self.assertIsNotNone(ps[0].lifetime)
        self.assertEqual(ps[0].charge, 1)

        for self.api.pedantic in [True, False]:
            p = self.api.get_particle_by_mcid(323)
            self.assertEqual(len(list(p.masses())), 3)
            self.assertEqual(len(list(p.widths())), 2)
            self.assertEqual(len(list(p.lifetimes())), 0)
            self.assertEqual(p.charge, 1.0)
        self.api.pedantic = False
        p = self.api.get_particle_by_mcid(323)
        self.assertEqual(round(p.mass, 3), 0.892)
        self.assertEqual(round(p.width, 4), 0.0514)
        self.assertEqual(round(p.lifetime * 1e23, 2), 1.28)
        self.api.pedantic = True
        p = self.api.get_particle_by_mcid(323)
        self.assertRaises(PdgAmbiguousValueError, lambda: p.mass)
        self.assertRaises(PdgAmbiguousValueError, lambda: p.width)
        self.assertRaises(PdgNoDataError, lambda: p.lifetime)

        for self.api.pedantic in [True, False]:
            p = self.api.get_particle_by_mcid(-323)
            self.assertEqual(len(list(p.masses())), 3)
            self.assertEqual(len(list(p.widths())), 2)
            self.assertEqual(len(list(p.lifetimes())), 0)
            self.assertEqual(p.charge, -1.0)
        self.api.pedantic = False
        p = self.api.get_particle_by_mcid(-323)
        self.assertEqual(round(p.mass, 3), 0.892)
        self.assertEqual(round(p.width, 4), 0.0514)
        self.assertEqual(round(p.lifetime * 1e23, 2), 1.28)
        self.api.pedantic = True
        p = self.api.get_particle_by_mcid(-323)
        self.assertRaises(PdgAmbiguousValueError, lambda: p.mass)
        self.assertRaises(PdgAmbiguousValueError, lambda: p.width)
        self.assertRaises(PdgNoDataError, lambda: p.lifetime)

        for self.api.pedantic in [True, False]:
            p = self.api.get_particle_by_mcid(313)
            self.assertEqual(len(list(p.masses())), 2)
            self.assertEqual(len(list(p.widths())), 1)
            self.assertEqual(len(list(p.lifetimes())), 0)
            self.assertEqual(p.charge, 0.0)
        self.api.pedantic = False
        p = self.api.get_particle_by_mcid(313)
        self.assertEqual(round(p.mass, 3), 0.896)
        self.assertEqual(round(p.width, 4), 0.0473)
        self.assertEqual(round(p.lifetime * 1e23, 2), 1.39)
        self.api.pedantic = True
        p = self.api.get_particle_by_mcid(313)
        self.assertRaises(PdgAmbiguousValueError, lambda: p.mass)
        self.assertEqual(round(p.width, 4), 0.0473)
        self.assertRaises(PdgNoDataError, lambda: p.lifetime)

    def test_decay_W2PiGamma(self):
        decay = self.api.get('S043.6')
        self.assertIsInstance(decay, PdgBranchingFraction)
        self.assertTrue(decay.is_limit)
        self.assertEqual(decay.value, 1.9e-6)
        ps = decay.decay_products
        self.assertTrue(isinstance(p, PdgDecayProduct) for p in ps)

        self.assertEqual(ps[0].multiplier, 1)
        self.assertIsNone(ps[0].subdecay)
        self.assertEqual(ps[0].item.name, 'pi+')
        self.assertEqual(ps[0].item.item_type, 'P')
        self.assertTrue(ps[0].item.has_particle)
        piplus = ps[0].item.particle
        self.assertIsInstance(piplus, PdgParticle)
        self.assertEqual(piplus.pdgid, 'S008/%s' % self.api.default_edition)

        self.assertEqual(ps[1].multiplier, 1)
        self.assertIsNone(ps[1].subdecay)
        self.assertEqual(ps[1].item.name, 'gamma')
        self.assertEqual(ps[1].item.item_type, 'P')
        self.assertTrue(ps[1].item.has_particle)
        gamma = ps[1].item.particle
        self.assertIsInstance(gamma, PdgParticle)
        self.assertEqual(gamma.pdgid, 'S000/%s' % self.api.default_edition)

    def test_decay_Z2JpsiX(self):
        decay = self.api.get('S044.23')
        self.assertIsInstance(decay, PdgBranchingFraction)
        self.assertFalse(decay.is_limit)
        self.assertEqual(decay.value, 0.00351170065655418)
        ps = decay.decay_products
        self.assertTrue(isinstance(p, PdgDecayProduct) for p in ps)

        self.assertEqual(ps[0].multiplier, 1)
        self.assertIsNone(ps[0].subdecay)
        self.assertEqual(ps[0].item.name, 'J/psi(1S)')
        self.assertEqual(ps[0].item.item_type, 'P')
        self.assertTrue(ps[0].item.has_particle)
        jpsi = ps[0].item.particle
        self.assertIsInstance(jpsi, PdgParticle)
        self.assertEqual(jpsi.pdgid, 'M070/%s' % self.api.default_edition)

        self.assertEqual(ps[1].multiplier, 1)
        self.assertIsNone(ps[1].subdecay)
        self.assertEqual(ps[1].item.name, 'X')
        self.assertEqual(ps[1].item.item_type, 'I')
        self.assertFalse(ps[1].item.has_particle)

    # This tests the use of PDGITEM_MAP to get from Z to Z0
    def test_decay_H2ZGamma(self):
        decay = self.api.get('S126.6')
        self.assertIsInstance(decay, PdgBranchingFraction)
        self.assertFalse(decay.is_limit)
        self.assertEqual(decay.value, 0.0034)
        ps = decay.decay_products
        self.assertTrue(isinstance(p, PdgDecayProduct) for p in ps)

        self.assertEqual(ps[0].multiplier, 1)
        self.assertIsNone(ps[0].subdecay)
        self.assertEqual(ps[0].item.name, 'Z')
        self.assertEqual(ps[0].item.item_type, 'G')
        self.assertTrue(ps[0].item.has_particle)
        Z = ps[0].item.particle
        self.assertIsInstance(Z, PdgParticle)
        self.assertEqual(Z.pdgid, 'S044/%s' % self.api.default_edition)

        self.assertEqual(ps[1].multiplier, 1)
        self.assertIsNone(ps[1].subdecay)
        self.assertEqual(ps[1].item.name, 'gamma')
        self.assertEqual(ps[1].item.item_type, 'P')
        self.assertTrue(ps[1].item.has_particle)
        gamma = ps[1].item.particle
        self.assertIsInstance(gamma, PdgParticle)
        self.assertEqual(gamma.pdgid, 'S000/%s' % self.api.default_edition)
