"""
Test cases for the PDG data.
"""
from __future__ import print_function

import unittest

import pdg
from pdg.errors import PdgAmbiguousValueError, PdgInvalidPdgIdError
from pdg.data import PdgConvertedValue, PdgMass
from pdg.particle import PdgParticle, PdgParticleList
from pdg.decay import PdgBranchingFraction


class TestData(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.api = pdg.connect()

    def test_exception(self):
        self.assertRaises(PdgInvalidPdgIdError, self.api.get, 'nonexistent')

    def test_edition(self):
        self.assertEqual(self.api.get('s008').edition, self.api.default_edition)
        if '2018' not in self.api.editions:
            return
        self.assertEqual(self.api.get('s008/2018').pdgid, 'S008/2018')
        self.assertEqual(self.api.get('s008/2018').baseid, 'S008')
        self.assertEqual(self.api.get('s008/2018').get_parent_pdgid(), None)
        self.assertEqual(self.api.get('s008.1/2018').get_parent_pdgid(), 'S008/2018')

    def test_charged_pion_2022(self):
        if '2022' not in self.api.editions:
            return
        pion = self.api.get('S008/2022')[0]
        self.assertIsInstance(pion, PdgParticle)
        self.assertEqual(pion.pdgid, 'S008/2022')
        self.assertEqual(pion.edition, '2022')
        self.assertEqual(pion.description, 'pi+-')
        self.assertEqual(pion.data_type, 'PART')
        self.assertEqual(pion.get_parent_pdgid(), None)
        self.assertEqual(pion.name, 'pi+')
        self.assertEqual(pion.mcid, 211)
        self.assertEqual(pion.charge, 1.0)
        self.assertEqual(pion.quantum_I, '1')
        self.assertEqual(pion.quantum_G, '-')
        self.assertEqual(pion.quantum_J, '0')
        self.assertEqual(pion.quantum_P, '-')
        self.assertEqual(pion.quantum_C, None)
        self.assertEqual(sum(1 for _ in pion.properties(require_summary_data=False)), 12)
        self.assertEqual(sum(1 for _ in pion.properties(require_summary_data=True)), 10)
        self.assertEqual(sum(1 for _ in pion.exclusive_branching_fractions()), 9)
        self.assertEqual(sum(1 for _ in pion.exclusive_branching_fractions(include_subdecays=True)), 11)

    def test_charged_pion_mass_2022(self):
        if '2022' not in self.api.editions:
            return
        m = self.api.get('S008M/2022')
        self.assertEqual(m._count_data_entries('S008m', 2022), 2)
        self.assertIsInstance(m, PdgMass)
        self.assertEqual(m.description, 'pi+- MASS')
        self.assertEqual(m.n_summary_table_values(), 1)
        self.assertEqual(m.get_parent_pdgid(), 'S008/2022')
        self.assertRaises(PdgAmbiguousValueError, lambda: m.get_particle())
        self.assertIsInstance(m.get_particles(), PdgParticleList)
        self.assertIsInstance(m.get_particles()[0], PdgParticle)
        # Enable following tests only after IN_SUMMARY_TABLE is properly set
        best_value = m.best_summary()
        self.assertEqual(best_value.in_summary_table, True)
        self.assertEqual(round(best_value.value, 5), 139.57039)
        self.assertEqual(round(best_value.error_positive, 5), 0.00018)
        self.assertEqual(round(best_value.error_negative, 5), 0.00018)
        self.assertEqual(round(best_value.error,5), 0.00018)
        self.assertEqual(round(best_value.scale_factor, 1), 1.8)
        self.assertEqual(best_value.units, 'MeV')
        self.assertEqual(best_value.display_value_text, '139.57039+-0.00018')
        self.assertEqual(best_value.value_type_key, 'FC')
        self.assertEqual(str(best_value).strip(), '139.57039+-0.00018   OUR FIT')
        best_value_GeV = PdgConvertedValue(best_value, 'GeV')
        self.assertEqual(round(best_value_GeV.value, 8), 0.13957039)
        self.assertEqual(round(best_value_GeV.error_positive, 8), 1.8E-7)
        self.assertEqual(round(best_value_GeV.error_negative, 8), 1.8E-7)
        self.assertEqual(round(best_value_GeV.scale_factor, 1), 1.8)
        self.assertEqual(best_value_GeV.units, 'GeV')

    def test_neutral_pion_decay_2022(self):
        if '2022' not in self.api.editions:
            return
        b = self.api.get('S009.1/2022')
        self.assertIsInstance(b, PdgBranchingFraction)
        self.assertEqual(b.description, 'pi0 --> 2gamma')
        self.assertEqual(b.n_summary_table_values(), 1)
        self.assertEqual(b.get_parent_pdgid(), 'S009/2022')
        self.assertIsInstance(b.get_particle(), PdgParticle)
        self.assertEqual(b.is_subdecay, False)
        self.assertEqual(b.subdecay_level, 0)
        best_value = b.best_summary()
        self.assertEqual(best_value.in_summary_table, True)
        self.assertEqual(round(best_value.value, 5), 0.98823)
        self.assertEqual(round(best_value.error_positive, 5), 0.00034)
        self.assertEqual(round(best_value.error_negative, 5), 0.00034)
        self.assertEqual(round(best_value.scale_factor, 1), 1.5)
        self.assertEqual(best_value.units, '')
        self.assertEqual(best_value.display_value_text, '(98.823+-0.034)E-2')
        self.assertEqual(best_value.value_type_key, 'FC')
        # self.assertEqual(best_value.display_in_percent, True)   # FIXME

    def test_subdecay_modes(self):
        self.assertEqual(self.api.get('S008.1').is_subdecay, False)
        self.assertEqual(self.api.get('S008.3').is_subdecay, True)
        self.assertEqual(self.api.get('S008.1').subdecay_level, 0)
        self.assertEqual(self.api.get('S008.3').subdecay_level, 1)

    def test_limit_2022(self):
        if '2022' not in self.api.editions:
            return
        self.assertEqual(self.api.get('S008.11').best_summary().is_limit, True)
        self.assertEqual(self.api.get('S008.11').best_summary().is_upper_limit, True)
        self.assertEqual(self.api.get('S008.11').best_summary().is_lower_limit, False)
        self.assertEqual(self.api.get('S008FV').best_summary().is_limit, False)
        self.assertEqual(self.api.get('S008FV').best_summary().is_upper_limit, False)
        self.assertEqual(self.api.get('S008FV').best_summary().is_lower_limit, False)

    def test_error_2022(self):
        if '2022' not in self.api.editions:
            return
        self.assertEqual(self.api.get('S066M2E/2022').best_summary().error, None)
        self.assertEqual(self.api.get('M013.4/2022').best_summary().error, 0.0218379495175522 )

    def test_data_flags(self):
        self.assertEqual(self.api.get('S003AMU').data_flags, 'As')
        self.assertEqual(self.api.get('S004AMU').data_flags, 'As')
        self.assertEqual(self.api.get('S016AMU').data_flags, 'As')
        self.assertEqual(self.api.get('S017AMU').data_flags, 'A0s')
        self.assertEqual(self.api.get('Q007TP').data_flags, 's')
        self.assertEqual(self.api.get('Q007TP2').data_flags, 's')
        self.assertEqual(self.api.get('Q007TP4').data_flags, 'D')

    def test_old_bugs(self):
        # Check fix for metadata bug in v0.0.5
        self.assertIsNotNone(self.api.get('S086DRA').best_summary())
        self.assertIsNotNone(self.api.get('S086DGS').best_summary())

    def test_HFLAV_comment(self):
        if int(self.api.default_edition) >= 2024:
            self.assertEqual(self.api.get('S042T').comment,
                             '(Produced by HFLAV)')

if __name__ == '__main__':
    unittest.main()
