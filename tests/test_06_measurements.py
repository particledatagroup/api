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

        m_msmts = list(muon.mass_measurements(require_summary_data=False))
        t_msmts = list(muon.lifetime_measurements(require_summary_data=False))

        mass = next(m for m in m_msmts
                    if m.inline_comment == '2018 CODATA value'
                    and m.pdgid == 'S004M')
        self.assertEqual(mass.pdgid, 'S004M')
        self.assertEqual(mass.event_count, '')
        self.assertIsNone(mass.confidence_level)
        self.assertEqual(mass.technique, 'RVUE')
        self.assertEqual(mass.charge, '')
        self.assertFalse(mass.changebar)
        self.assertEqual(mass.inline_comment, '2018 CODATA value')

        ref = mass.reference
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
        self.assertEqual(value.value_name, 'Value')
        self.assertEqual(value.unit_text, 'MeV')
        self.assertEqual(value.unit_tex, 'MeV')
        self.assertEqual(value.display_value_text, '105.6583755 +-0.0000023')
        self.assertEqual(value.display_power_of_ten, 0)
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

        lifetime = next(t for t in t_msmts if t.inline_comment == 'Surface mu+ at PSI')
        self.assertEqual(lifetime.pdgid, 'S004T')
        self.assertEqual(lifetime.event_count, '')
        self.assertIsNone(lifetime.confidence_level)
        self.assertEqual(lifetime.technique, 'CNTR')
        self.assertEqual(lifetime.charge, '+')
        self.assertFalse(lifetime.changebar)
        self.assertEqual(lifetime.inline_comment, 'Surface mu+ at PSI')

        ref = lifetime.reference
        self.assertEqual(ref.publication_name, 'PR D87 052003')
        self.assertEqual(ref.publication_year, 2013)
        self.assertEqual(
            ref.title,
            'Detailed Report of the MuLan Measurement of the Positive Muon Lifetime and Determination of the Fermi Constant')
        self.assertEqual(ref.doi, '10.1103/PhysRevD.87.052003')
        self.assertEqual(ref.inspire_id, '1198154')

        values = list(lifetime.values())
        self.assertEqual(len(values), 1)
        value = values[0]
        self.assertEqual(value.measurement.id, lifetime.id)
        self.assertEqual(value.value_name, 'Value')
        self.assertEqual(value.unit_text, 's')
        self.assertEqual(value.unit_tex, 's')
        self.assertEqual(value.display_value_text, '2.1969803 +-0.0000021 +-0.0000007')
        self.assertEqual(value.display_power_of_ten, -6)
        self.assertFalse(value.display_in_percent)
        self.assertIsNone(value.limit_type)
        self.assertTrue(value.used_in_average)
        self.assertTrue(value.used_in_fit)
        self.assertEqual(round(value.value*1e6, 7), 2.1969803)
        self.assertEqual(round(value.error_positive*1e12, 5), 2.21359)
        self.assertEqual(value.error_negative, value.error_positive)
        self.assertEqual(round(value.stat_error_positive*1e13), 21)
        self.assertEqual(value.stat_error_negative, value.stat_error_positive)
        self.assertEqual(round(value.syst_error_positive*1e13), 7)
        self.assertEqual(value.syst_error_negative, value.syst_error_positive)

    # TODO:
    # - particle that has a width instead of a lifetime
    # - footnote
    # - measurements below the line
    # - multi-column measurements
    # - limits
