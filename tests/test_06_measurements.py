#!/usr/bin/env python

"""
Test cases for measurements.
"""
from __future__ import print_function

import unittest

import pdg


class TestMeasurements(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect()

    def test_muon(self):
        muon = self.api.get_particle_by_name('mu-')

        m_msmts = list(muon.mass_measurements())
        t_msmts = list(muon.lifetime_measurements())

        mass = next(m for m in m_msmts if m.id == 58595)
        self.assertEqual(mass.pdgid, 'S004M')
        self.assertIsNone(mass.event_count)
        self.assertIsNone(mass.confidence_level)
        self.assertEqual(mass.technique, 'RVUE')
        self.assertIsNone(mass.charge)
        self.assertFalse(mass.changebar)
        self.assertEqual(mass.inline_comment, '2018 CODATA value')
        self.assertEqual(mass.when_added, 'FIXME')

        ref = mass.reference
        self.assertEqual(ref.id, 61422)
        self.assertEqual(ref.publication_name, 'RMP 93 025010')
        self.assertEqual(ref.publication_year, 2021)
        self.assertEqual(
            ref.title,
            'CODATA recommended values of the fundamental physical constants: 2018')
        self.assertEqual(ref.doi, '10.1103/RevModPhys.93.025010')
        self.assertEqual(ref.inspire_id, '1898737')

        values = list(mass.values())
        self.assertEqual(len(values), 1)
        value = values[0]
        self.assertEqual(value.measurement.id, mass.id)
        self.assertEqual(value.value_name, 'mass') # ???
        self.assertEqual(value.unit_text, 'MeV')
        self.assertEqual(value.unit_tex, 'MeV')
        self.assertIsNone(value.display_power_text)
        self.assertIsNone(value.display_power_of_ten)
        self.assertFalse(value.display_in_percent)
        self.assertIsNone(value.limit_type)
        self.assertTrue(value.used_in_average)
        self.assertTrue(value.used_in_fit)
        self.assertEqual(round(value.value, 7), 105.6583755)
        self.assertEqual(round(value.error_positive, 7), 0.0000023)
        self.assertEqual(value.error_negative, value.error_positive)
        self.assertIsNone(value.stat_error_positive)
        self.assertIsNone(value.stat_error_negative)
        self.assertIsNone(value.syst_error_positive)
        self.assertIsNone(value.syst_error_negative)

        lifetime = next(t for t in t_msmts if t.id == 43631)
        self.assertEqual(lifetime.pdgid, 'S004T')
        self.assertIsNone(lifetime.event_count)
        self.assertIsNone(lifetime.confidence_level)
        self.assertEqual(lifetime.technique, 'CNTR')
        self.assertEqual(lifetime.charge, '+')
        self.assertFalse(lifetime.changebar)
        # FIXME: Should we parse the macros and provide ascii + tex comments?
        self.assertEqual(lifetime.inline_comment, 'Surface #p{mu+} at PSI')
        self.assertEqual(lifetime.when_added, 'FIXME')

        ref = lifetime.reference
        self.assertEqual(ref.id, 55129)
        self.assertEqual(ref.publication_name, 'PR D87 052003')
        self.assertEqual(ref.publication_year, 2013)
        self.assertEqual(
            ref.title,
            'Detailed Report of the MuLan Measurement of the Positi ve Muon Lifetime and Determination of the Fermi Constant')
        self.assertEqual(ref.doi, '10.1103/PhysRevD.87.052003')
        self.assertEqual(ref.inspire_id, '1198154')

        values = list(lifetime.values())
        self.assertEqual(len(values), 1)
        value = values[0]
        self.assertEqual(value.measurement.id, lifetime.id)
        self.assertEqual(value.value_name, 'lifetime') # ???
        self.assertEqual(value.unit_text, '1E-6 s')    # ???
        self.assertEqual(value.unit_tex, '10^{-6} s')
        self.assertEqual(value.display_power_text, 'FIXME')
        self.assertEqual(value.display_power_of_ten, 'FIXME')
        self.assertFalse(value.display_in_percent)
        self.assertIsNone(value.limit_type)
        self.assertTrue(value.used_in_average)
        self.assertTrue(value.used_in_fit)
        # FIXME: Units? (Apply 1E6?)
        self.assertEqual(round(value.value, 7), 2.1969803)
        self.assertEqual(round(value.error_positive*1e6, 5), 2.21359)
        self.assertEqual(value.error_negative, value.error_positive)
        self.assertEqual(round(value.stat_error_positive*1e6), 21)
        self.assertEqual(value.stat_error_negative, value.stat_error_positive)
        self.assertEqual(round(value.syst_error_positive*1e6), 7)
        self.assertEqual(value.syst_error_negative, value.syst_error_positive)

    # TODO:
    # - particle that has a width instead of a lifetime
    # - stat/syst errors
    # - footnote
    # - measurements below the line
    # - multi-column measurements
    # - limits
